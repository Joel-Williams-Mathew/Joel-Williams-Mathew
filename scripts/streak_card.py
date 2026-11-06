#!/usr/bin/env python3
"""
Generate the GitHub streak card as an SVG.

Uses the GitHub GraphQL API when a token is available, so contributions to
PRIVATE repositories are counted. Falls back to the public contributions page
when no token is present.

Token is read from (in order):
    GH_TOKEN   - repo secret, preferred
    GITHUB_TOKEN - the Actions default token (public data only)
"""
import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.request

USER = os.environ.get("GH_USER", "Joel-Williams-Mathew")
OUT = os.environ.get("STREAK_OUT", "streak.svg")
ACCOUNT_START = os.environ.get("ACCOUNT_START", "2024-08-26")

# palette
BG = "#0D1117"
RING = "#FF6B35"
FIRE = "#FF6B35"
LABEL = "#FFB454"
NUM = "#F5E6CC"
MUTED = "#8B949E"


# ---------------------------------------------------------------------------
# data sources
# ---------------------------------------------------------------------------
def fetch_graphql(token):
    """Return ({date: count}, total) for the FULL history via GraphQL.

    contributionCollection only returns 12 months at a time, so we request one
    window per year and sum them. With a token that can see private
    contributions, this is the complete picture.
    """
    query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                date
                contributionCount
              }
            }
          }
        }
      }
    }
    """
    body = json.dumps({"query": query, "variables": {"login": USER}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "streak-card/2.0",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read().decode("utf-8"))

    if "errors" in payload:
        raise RuntimeError(payload["errors"])

    cal = payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    days = {}
    for week in cal["weeks"]:
        for day in week["contributionDays"]:
            days[day["date"]] = day["contributionCount"]
    return days, cal["totalContributions"]


def fetch_year(year):
    """Return (headline_total, {date: count}) for one calendar year.

    GitHub exposes a separate calendar per year via from/to query params,
    which is the only way to total the account's whole history.
    """
    url = (f"https://github.com/users/{USER}/contributions"
           f"?from={year}-01-01&to={year}-12-31")
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; streak-card/3.0)",
    })
    html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")

    headline = None
    m = re.search(r"([\d,]+)\s+contributions?\s+in\s+" + str(year), html)
    if m:
        headline = int(m.group(1).replace(",", ""))

    dates = re.findall(r'data-date="(\d{4}-\d{2}-\d{2})"', html)
    tips = re.findall(r"<tool-tip[^>]*>([^<]*)</tool-tip>", html)

    days = {}
    counts = []
    for tip in tips:
        c = re.search(r"(\d+|No)\s+contribution", tip)
        if c:
            counts.append(0 if c.group(1) == "No" else int(c.group(1)))

    for d, c in zip(dates, counts):
        days[d] = c

    if headline is None:
        headline = sum(days.values())

    return headline, days


def fetch_all_years():
    """Sum every year GitHub has a calendar for (2024 -> current)."""
    start_year = int(ACCOUNT_START[:4])
    now_year = dt.date.today().year

    all_days = {}
    total = 0
    found = []

    for year in range(start_year, now_year + 1):
        try:
            head, days = fetch_year(year)
        except Exception as exc:  # noqa: BLE001
            print(f"  {year}: failed ({exc})", file=sys.stderr)
            continue
        all_days.update(days)
        total += head
        found.append(f"{year}={head}")

    print("  per year: " + ", ".join(found), file=sys.stderr)
    return all_days, total


# ---------------------------------------------------------------------------
# streak maths
# ---------------------------------------------------------------------------
def fmt(d):
    return f"{d.strftime('%b')} {d.day}"


def compute(days, total):
    ordered = sorted(days.items())
    if not ordered:
        return None

    today = dt.date.today()

    # Drop future-padded days that GitHub includes when we request a whole year,
    # otherwise the streak walk starts on empty dates.
    ordered = [(d, c) for d, c in ordered
               if dt.date.fromisoformat(d) <= today]
    if not ordered:
        return None

    dates = [dt.date.fromisoformat(d) for d, _ in ordered]

    # current streak - allow today to be empty without breaking it
    i = len(ordered) - 1
    if i >= 0 and ordered[i][1] == 0 and dates[i] == today:
        i -= 1
    cur = 0
    while i >= 0 and ordered[i][1] > 0:
        cur += 1
        i -= 1

    # length of the current run, for the date range
    if cur:
        end_i = len(ordered) - 1
        if ordered[end_i][1] == 0 and dates[end_i] == today:
            end_i -= 1
        end = dates[end_i]
        start = end - dt.timedelta(days=cur - 1)
        cur_range = f"{fmt(start)} - {fmt(end)}"
    else:
        cur_range = "no current streak"

    # longest streak + its range
    longest = 0
    run = 0
    best_end_i = None
    for idx, (_, c) in enumerate(ordered):
        if c > 0:
            run += 1
            if run > longest:
                longest = run
                best_end_i = idx
        else:
            run = 0

    if best_end_i is not None:
        best_end = dates[best_end_i]
        best_start = best_end - dt.timedelta(days=longest - 1)
        long_range = f"{fmt(best_start)} - {fmt(best_end)}"
    else:
        long_range = "-"

    start_date = dt.date.fromisoformat(ACCOUNT_START)
    span = f"{fmt(start_date)}, {start_date.year} - Present"

    return total, cur, longest, cur_range, long_range, span


# ---------------------------------------------------------------------------
# rendering
# ---------------------------------------------------------------------------
def build_svg(total, cur, longest, cur_range, long_range, span):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="495" height="195" viewBox="0 0 495 195" role="img" aria-label="GitHub streak: {total} total contributions, current streak {cur}, longest streak {longest}">
  <rect x="0.5" y="0.5" width="494" height="194" rx="4.5" fill="{BG}" stroke="{RING}"/>
  <g font-family="'Segoe UI', Ubuntu, sans-serif">
    <text x="82" y="60" font-size="28" font-weight="700" fill="{NUM}" text-anchor="middle">{total}</text>
    <text x="82" y="86" font-size="14" fill="{LABEL}" text-anchor="middle">Total Contributions</text>
    <text x="82" y="112" font-size="11" fill="{MUTED}" text-anchor="middle">{span}</text>

    <line x1="165" y1="28" x2="165" y2="167" stroke="#333" stroke-width="1"/>
    <line x1="330" y1="28" x2="330" y2="167" stroke="#333" stroke-width="1"/>

    <path d="M 224 50 A 31 31 0 1 0 270 50"
          fill="none" stroke="{RING}" stroke-width="5" stroke-linecap="round"/>
    <text x="247" y="80" font-size="26" font-weight="700" fill="{NUM}" text-anchor="middle">{cur}</text>
    <g transform="translate(247,36)">
      <path d="M0,-13 C 5,-5 8,-2 8,3 A 8,8 0 0 1 -8,3 C -8,-2 -5,-5 0,-13 Z" fill="{FIRE}"/>
      <path d="M0,-4 C 2.4,0 3.6,1.6 3.6,3.4 A 3.6,3.6 0 0 1 -3.6,3.4 C -3.6,1.6 -2.4,0 0,-4 Z"
            fill="#FFD8A8" opacity="0.9"/>
    </g>
    <text x="247" y="120" font-size="14" fill="{LABEL}" text-anchor="middle">Current Streak</text>
    <text x="247" y="142" font-size="11" fill="{MUTED}" text-anchor="middle">{cur_range}</text>

    <text x="412" y="60" font-size="28" font-weight="700" fill="{NUM}" text-anchor="middle">{longest}</text>
    <text x="412" y="86" font-size="14" fill="{LABEL}" text-anchor="middle">Longest Streak</text>
    <text x="412" y="112" font-size="11" fill="{MUTED}" text-anchor="middle">{long_range}</text>
  </g>
</svg>
'''


def main():
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
    source = "public page"

    days = None
    total = None

    if token:
        try:
            days, total = fetch_graphql(token)
            source = "GraphQL (authenticated - includes private)"
        except Exception as exc:  # noqa: BLE001
            print(f"graphql failed, falling back: {exc}", file=sys.stderr)

    if days is None:
        try:
            days, total = fetch_all_years()
            source = "public calendars (all years)"
        except Exception as exc:  # noqa: BLE001
            print(f"public fetch failed: {exc}", file=sys.stderr)
            return 0

    print(f"source: {source}", file=sys.stderr)
    print(f"days: {len(days)}  sum: {sum(days.values())}  reported: {total}", file=sys.stderr)

    if not days:
        print("no data - leaving streak.svg unchanged", file=sys.stderr)
        return 0

    result = compute(days, total)
    if not result:
        print("could not compute", file=sys.stderr)
        return 0

    t, cur, longest, cur_range, long_range, span = result
    print(f"total={t} current={cur} longest={longest}", file=sys.stderr)

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(build_svg(t, cur, longest, cur_range, long_range, span))

    print(f"wrote {OUT}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""
Fetch the GitHub contribution streak and write it as an SVG.

Produces the same visual as streak-stats.demolab.com but hosted in this repo,
so GitHub's image proxy has nothing external to cache stale.

Reads contribution data from the public GitHub contributions page, which does
not require authentication.
"""
import datetime as dt
import json
import re
import sys
import urllib.request

USER = "Joel-Williams-Mathew"
# first contribution date on the profile (set once)
ACCOUNT_START = "2024-08-26"
OUT = "streak.svg"

# palette (matches the site)
BG = "#0D1117"
RING = "#FF6B35"
FIRE = "#FF6B35"
LABEL = "#FFB454"
NUM = "#F5E6CC"
MUTED = "#8B949E"


def fetch_contributions():
    """Return {date: count} from the public contributions calendar."""
    url = f"https://github.com/users/{USER}/contributions"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; streak-card/1.0)",
        "Accept": "text/html",
    })
    html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")

    # each day is a <td> with data-date and a tooltip containing the count
    days = {}
    for m in re.finditer(
        r'data-date="(\d{4}-\d{2}-\d{2})"[^>]*?(?:data-level="(\d)")?', html
    ):
        days[m.group(1)] = 0

    # tooltips look like: <tool-tip ...>12 contributions on November 5th.</tool-tip>
    # they appear after each day cell, so pair them up in document order
    dates = re.findall(r'data-date="(\d{4}-\d{2}-\d{2})"', html)
    tips = re.findall(r'<tool-tip[^>]*>([^<]*)</tool-tip>', html)

    counts = []
    for tip in tips:
        n = re.search(r"(\d+|No)\s+contribution", tip)
        if n:
            counts.append(0 if n.group(1) == "No" else int(n.group(1)))

    for d, c in zip(dates, counts):
        days[d] = c

    return days


def compute(days):
    if not days:
        return None, None, None
    ordered = sorted(days.items())
    today = dt.date.today()
    total = sum(days.values())

    # current streak: walk back from today (or yesterday if today is 0 so far)
    dates = [dt.date.fromisoformat(d) for d, _ in ordered]
    cur = 0
    i = len(ordered) - 1
    # allow today to be empty without breaking the streak
    if i >= 0 and ordered[i][1] == 0 and dates[i] == today:
        i -= 1
    while i >= 0 and ordered[i][1] > 0:
        cur += 1
        i -= 1

    # longest streak
    longest = 0
    run = 0
    for _, c in ordered:
        if c > 0:
            run += 1
            longest = max(longest, run)
        else:
            run = 0

    # current streak date range
    def fmt(d):
        return d.strftime("%b %-d") if sys.platform != "win32" else d.strftime("%b %d").replace(" 0", " ")

    if cur:
        end = dates[len(ordered) - 1] if ordered[-1][1] > 0 else dates[len(ordered) - 2]
        start = end - dt.timedelta(days=cur - 1)
        cur_range = f"{fmt(start)} - {fmt(end)}"
    else:
        cur_range = "no current streak"

    # longest streak range
    best_end = None
    run = 0
    for d, c in ordered:
        if c > 0:
            run += 1
            if run == longest:
                best_end = d
        else:
            run = 0
    if best_end:
        best_end_d = dt.date.fromisoformat(best_end)
        best_start = best_end_d - dt.timedelta(days=longest - 1)
    else:
        best_start = None
    long_range = f"{fmt(best_start)} - {fmt(best_end_d)}" if best_start else "-"

    # The contributions calendar only covers ~12 months, so its earliest date
    # is NOT when the account started. Use the account creation year instead.
    start = dt.date.fromisoformat(ACCOUNT_START)
    span = f"{fmt(start)}, {start.year} - Present"

    return total, cur, longest, cur_range, long_range, span


def build_svg(total, cur, longest, cur_range, long_range, span):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="495" height="195" viewBox="0 0 495 195" role="img" aria-label="GitHub streak: {total} total contributions, current streak {cur}, longest streak {longest}">
  <rect x="0.5" y="0.5" width="494" height="194" rx="4.5" fill="{BG}" stroke="{RING}"/>
  <g font-family="'Segoe UI', Ubuntu, sans-serif">
    <text x="82" y="60" font-size="28" font-weight="700" fill="{NUM}" text-anchor="middle">{total}</text>
    <text x="82" y="86" font-size="14" fill="{LABEL}" text-anchor="middle">Total Contributions</text>
    <text x="82" y="112" font-size="11" fill="{MUTED}" text-anchor="middle">{span}</text>

    <line x1="165" y1="28" x2="165" y2="167" stroke="#333" stroke-width="1"/>
    <line x1="330" y1="28" x2="330" y2="167" stroke="#333" stroke-width="1"/>

    <!-- streak ring, open at the top so the flame sits in the gap -->
    <path d="M 224 50 A 31 31 0 1 0 270 50"
          fill="none" stroke="{RING}" stroke-width="5" stroke-linecap="round"/>
    <text x="247" y="80" font-size="26" font-weight="700" fill="{NUM}" text-anchor="middle">{cur}</text>
    <!-- flame, centred in the ring opening -->
    <g transform="translate(247,36)">
      <path d="M0,-13 C 5,-5 8,-2 8,3 A 8,8 0 0 1 -8,3 C -8,-2 -5,-5 0,-13 Z"
            fill="{FIRE}"/>
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
    try:
        days = fetch_contributions()
    except Exception as exc:
        print(f"fetch failed: {exc}", file=sys.stderr)
        return 0

    print(f"days parsed: {len(days)}", file=sys.stderr)
    if not days:
        print("no contribution days found - leaving streak.svg untouched", file=sys.stderr)
        return 0

    result = compute(days)
    if not result or result[0] is None:
        print("could not compute streaks", file=sys.stderr)
        return 0

    total, cur, longest, cur_range, long_range, span = result
    print(f"total={total} current={cur} longest={longest}", file=sys.stderr)

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(build_svg(total, cur, longest, cur_range, long_range, span))

    print(f"wrote {OUT}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

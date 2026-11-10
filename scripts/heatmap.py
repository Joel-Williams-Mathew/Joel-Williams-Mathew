#!/usr/bin/env python3
"""
Self-hosted GitHub contribution heatmap (rolling ~1 year), rendered as an SVG.

Reads the public contribution calendars (one page per year, same trick the
streak card uses) and draws a GitHub-style grid of cells coloured on an
amber scale. Designed to sit in the profile README in place of the snake.
"""
import datetime as dt
import re
import sys
import urllib.request

USER = "Joel-Williams-Mathew"
OUT = "heat.svg"
YEARS = (2024, 2025, 2026)

# palette
BG = "#0D1117"
BORDER = "#FF6B35"
TEXT = "#F5E6CC"
MUTED = "#8B949E"
LABEL = "#FFB454"

# level thresholds: 0, 1-4, 5-9, 10-19, 20-39, 40+
LEVELS = [0, 1, 5, 10, 20, 40]
COLORS = ["#1b212b", "#4a2410", "#7a3411", "#b34a1a", "#FF6B35", "#FFB454"]


def fetch_year(year):
    url = (f"https://github.com/users/{USER}/contributions"
           f"?from={year}-01-01&to={year}-12-31")
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (compatible; heat-card/1.0)",
    })
    html = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    dates = re.findall(r'data-date="(\d{4}-\d{2}-\d{2})"', html)
    tips = re.findall(r"<tool-tip[^>]*>([^<]*)</tool-tip>", html)
    days = {}
    counts = []
    for tip in tips:
        m = re.search(r"(\d+|No)\s+contribution", tip)
        if m:
            counts.append(0 if m.group(1) == "No" else int(m.group(1)))
    for d, c in zip(dates, counts):
        days[d] = c
    return days


def level(count):
    if count <= 0:
        return 0
    if count < 5:
        return 1
    if count < 10:
        return 2
    if count < 20:
        return 3
    if count < 40:
        return 4
    return 5


def build_svg():
    days = {}
    for y in YEARS:
        try:
            days.update(fetch_year(y))
        except Exception as exc:  # noqa: BLE001
            print(f"year {y} failed: {exc}", file=sys.stderr)

    today = dt.date.today()

    ordered = sorted((d, c) for d, c in days.items() if dt.date.fromisoformat(d) <= today)
    if not ordered:
        raise SystemExit("no contribution data found")

    # rolling window: the last 53 weeks (Sunday-aligned)
    end_sunday = today - dt.timedelta(days=(today.weekday() + 1) % 7)
    start = end_sunday - dt.timedelta(weeks=52)

    # pad the grid to full weeks
    start -= dt.timedelta(days=start.weekday() + 1 if start.weekday() else 0)
    # ensure start is a Sunday
    if start.weekday() != 6:
        start = start - dt.timedelta(days=(start.weekday() + 1) % 7)

    cols = 53
    cell, gap = 11, 3
    grid_w = cols * (cell + gap) - gap
    left = 38
    top = 46
    width = left + grid_w + 14
    footer_y = top + 7 * (cell + gap) + 16
    height = footer_y + 12

    def cell_x(col):
        return left + col * (cell + gap)

    def cell_y(row):
        return top + row * (cell + gap)

    total_window = 0
    cells = []
    for col in range(cols):
        for row in range(7):
            d = start + dt.timedelta(days=col * 7 + row)
            if d > today:
                continue
            c = days.get(d.isoformat(), 0)
            total_window += c
            lv = level(c)
            fill = COLORS[lv]
            cells.append(
                f'<rect x="{cell_x(col)}" y="{cell_y(row)}" width="{cell}" height="{cell}" rx="2" fill="{fill}">'
                f'<title>{d.isoformat()}: {c} contributions</title></rect>'
            )

    # month labels
    months = []
    prev = None
    for col in range(cols):
        d = start + dt.timedelta(days=col * 7)
        m = d.strftime("%b")
        if m != prev:
            months.append(f'<text x="{cell_x(col)}" y="38" font-size="10" fill="{MUTED}">{m}</text>')
            prev = m

    daylabels = []
    for i, name in enumerate(["", "Mon", "", "Wed", "", "Fri", ""]):
        if name:
            daylabels.append(f'<text x="4" y="{cell_y(i) + 9}" font-size="9" fill="{MUTED}">{name}</text>')

    total_all = sum(c for _, c in ordered)

    legend = []
    legend.append(f'<text x="{width - 186}" y="{footer_y}" font-size="10" fill="{MUTED}" text-anchor="end">Less</text>')
    for i, col in enumerate(COLORS):
        legend.append(f'<rect x="{width - 178 + i * 14}" y="{footer_y - 10}" width="11" height="11" rx="2" fill="{col}"/>')
    legend.append(f'<text x="{width - 6}" y="{footer_y}" font-size="10" fill="{MUTED}" text-anchor="end">More</text>')

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Contribution heatmap, {total_all} contributions total">
  <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="6" fill="{BG}" stroke="{BORDER}"/>
  <g font-family="'Segoe UI', Ubuntu, sans-serif">
    <text x="{left}" y="17" font-size="10" fill="{LABEL}" letter-spacing="2">CONTRIBUTION HEAT</text>
    <text x="{width - 14}" y="17" font-size="10" fill="{MUTED}" text-anchor="end">{total_window} in the last year</text>
    {''.join(months)}
    {''.join(daylabels)}
    {''.join(cells)}
    <text x="{left}" y="{footer_y}" font-size="9" fill="{MUTED}">Aug 2024 - present · {total_all} total</text>
    {''.join(legend)}
  </g>
</svg>
'''
    return svg


def main():
    svg = build_svg()
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(svg)
    print(f"wrote {OUT}", file=sys.stderr)


if __name__ == "__main__":
    main()

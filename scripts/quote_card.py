#!/usr/bin/env python3
"""
Self-hosted weekly quote card for the profile README.

Picks the quote deterministically from the ISO week number, so a fresh
clone/push shows a new (well-chosen) line each week and never hits an
external service. Matches the streak card: dark bg, amber border.
"""
import datetime as dt
import sys

OUT = "quote.svg"

BG = "#0D1117"
BORDER = "#FF6B35"
NUM = "#F5E6CC"
LABEL = "#FFB454"
MUTED = "#8B949E"
FLAME = "#FF6B35"

QUOTES = [
    ("Talk is cheap. Show me the code.", "Linus Torvalds"),
    ("Make it work, make it right, make it fast.", "Kent Beck"),
    ("The best way to predict the future is to invent it.", "Alan Kay"),
    ("First, solve the problem. Then, write the code.", "John Johnson"),
    ("Programs must be written for people to read, not only machines to execute.", "Harold Abelson"),
    ("Perfection is reached when there is nothing left to take away.", "Saint-Exupery"),
    ("Stay hungry, stay foolish.", "Steve Jobs"),
    ("It's not a bug, it's an undocumented feature.", "old maxim"),
    ("Build it, break it, ship it. Repeat.", "Joel's creed"),
]


def pick_quote(today):
    week = today.isocalendar()[1]
    return QUOTES[week % len(QUOTES)]


def wrap(text, limit=44):
    words = text.split()
    lines, line = [], ""
    for w in words:
        trial = (line + " " + w).strip()
        if len(trial) <= limit:
            line = trial
        else:
            lines.append(line)
            line = w
    if line:
        lines.append(line)
    return lines


def build_svg():
    today = dt.date.today()
    quote, author = pick_quote(today)
    week = today.isocalendar()[1]
    lines = wrap(quote, limit=46)

    # vertical centering for up to 2 lines
    line_h = 27
    total_h = len(lines) * line_h
    start_y = 100 - total_h // 2 - 8

    text_lines = []
    for i, l in enumerate(lines):
        text_lines.append(
            f'<text x="247" y="{start_y + i * line_h}" '
            f'font-size="19" font-style="italic" fill="{NUM}" text-anchor="middle">{l}</text>'
        )

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="495" height="195" viewBox="0 0 495 195" role="img" aria-label="Quote: {quote} - {author}">
  <rect x="0.5" y="0.5" width="494" height="194" rx="4.5" fill="{BG}" stroke="{BORDER}"/>
  <g font-family="Georgia, 'Times New Roman', serif">
    <text x="30" y="66" font-size="64" fill="{FLAME}" opacity="0.30" font-family="Georgia, serif">&#8220;</text>
    {''.join(text_lines)}
    <text x="247" y="162" font-size="11" fill="{LABEL}" text-anchor="middle" letter-spacing="1">- {author.upper()}</text>
    <text x="18" y="183" font-size="8" fill="{MUTED}" letter-spacing="1">WEEK {week} &#183; ONE LINE AT A TIME</text>
  </g>
</svg>
'''


def main():
    svg = build_svg()
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(svg)
    print(f"wrote {OUT}", file=sys.stderr)


if __name__ == "__main__":
    main()

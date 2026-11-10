#!/usr/bin/env python3
"""
Self-hosted 'NOW' status card for the profile README - the three things
pulling your day right now, styled like the streak card. Edit the lines
and re-run; deterministic, no external dependencies.
"""
import sys

OUT = "now.svg"

BG = "#0D1117"
BORDER = "#FF6B35"
TEXT = "#F5E6CC"
LABEL = "#FFB454"
MUTED = "#8B949E"
DOT = "#FFB454"

ROWS = [
    ("BUILDING", "DUM-E - voice-first desktop automation"),
    ("EXPLORING", "generative AI, agents & RAG patterns"),
    ("SHIPPING", "ML pipelines & computer vision projects"),
]


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_svg():
    rows = []
    y = 72
    for tag, line in ROWS:
        rows.append(
            f'<text x="80" y="{y}" font-size="11" fill="{DOT}" '
            f'font-weight="700" letter-spacing="2">{esc(tag)}</text>'
        )
        rows.append(
            f'<text x="170" y="{y}" font-size="12" fill="{TEXT}">{esc(line)}</text>'
        )
        y += 34

    bullets = []
    y = 72
    for _ in ROWS:
        bullets.append(
            f'<circle cx="52" cy="{y - 4}" r="3.2" fill="{DOT}"/>'
        )
        y += 34

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="495" height="195" viewBox="0 0 495 195" role="img" aria-label="What Joel is doing now">
  <rect x="0.5" y="0.5" width="494" height="194" rx="4.5" fill="{BG}" stroke="{BORDER}"/>
  <g font-family="'Segoe UI', Ubuntu, sans-serif">
    <text x="30" y="30" font-size="10" fill="{LABEL}" letter-spacing="3">NOW</text>
    <text x="465" y="30" font-size="9" fill="{MUTED}" text-anchor="end" letter-spacing="1">LIVE FROM KERALA</text>
    {''.join(bullets)}
    {''.join(rows)}
  </g>
</svg>
'''


def main():
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(build_svg())
    print(f"wrote {OUT}", file=sys.stderr)


if __name__ == "__main__":
    main()

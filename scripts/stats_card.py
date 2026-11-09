#!/usr/bin/env python3
"""
Generate the GitHub stats card as an SVG.

Uses the GitHub GraphQL API when a token is present. With a repo-scoped
token (repo secret, e.g. GH_TOKEN), private repos are counted too. Without
a token we fail loudly and leave the existing card untouched.

Token read from (in order): GH_TOKEN, GITHUB_TOKEN.
"""
import json
import os
import sys
import urllib.request

USER = os.environ.get("GH_USER", "Joel-Williams-Mathew")
OUT = os.environ.get("STATS_OUT", "stats.svg")

# palette - same family as streak.svg
BG = "#0D1117"
RING = "#FF6B35"
LABEL = "#FFB454"
NUM = "#F5E6CC"
MUTED = "#8B949E"

QUERY = """
{ user(login: "%s") {
    pullRequests(first: 1) { totalCount }
    issues(first: 1) { totalCount }
    repositories(first: 100, ownerAffiliations: OWNER) {
      totalCount
      nodes {
        stargazerCount
        defaultBranchRef { target { ... on Commit { history { totalCount } } } }
      }
    }
  } }
""" % USER


def fetch():
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""
    if not token:
        raise RuntimeError("no token in GH_TOKEN / GITHUB_TOKEN")

    body = json.dumps({"query": QUERY}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={
            "Authorization": f"bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "stats-card/1.0",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        payload = json.loads(resp.read().decode("utf-8"))

    if "errors" in payload:
        raise RuntimeError(payload["errors"])

    user = payload["data"]["user"]
    repos = user["repositories"]["nodes"]

    commits = 0
    stars = 0
    for node in repos:
        target = node.get("defaultBranchRef") or {}
        target = target.get("target") or {}
        history = target.get("history") or {}
        commits += history.get("totalCount", 0)
        stars += node["stargazerCount"]

    return {
        "commits": commits,
        "prs": user["pullRequests"]["totalCount"],
        "issues": user["issues"]["totalCount"],
        "stars": stars,
        "repos": len(repos),
    }


def build_svg(commits, prs, issues, stars, repos):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="495" height="195" viewBox="0 0 495 195" role="img" aria-label="GitHub stats: {commits} total commits, {prs} pull requests, {stars} stars">
  <rect x="0.5" y="0.5" width="494" height="194" rx="4.5" fill="{BG}" stroke="{RING}"/>
  <g font-family="'Segoe UI', Ubuntu, sans-serif">
    <text x="247" y="28" font-size="10" fill="{MUTED}" text-anchor="middle" letter-spacing="2">GITHUB STATS</text>

    <line x1="165" y1="40" x2="165" y2="160" stroke="#333" stroke-width="1"/>
    <line x1="330" y1="40" x2="330" y2="160" stroke="#333" stroke-width="1"/>

    <text x="82" y="76" font-size="30" font-weight="700" fill="{NUM}" text-anchor="middle">{commits}</text>
    <text x="82" y="104" font-size="14" fill="{LABEL}" text-anchor="middle">Total Commits</text>
    <text x="82" y="128" font-size="11" fill="{MUTED}" text-anchor="middle">Across {repos} repos</text>

    <text x="247" y="76" font-size="30" font-weight="700" fill="{NUM}" text-anchor="middle">{prs}</text>
    <text x="247" y="104" font-size="14" fill="{LABEL}" text-anchor="middle">Pull Requests</text>
    <text x="247" y="128" font-size="11" fill="{MUTED}" text-anchor="middle">Opened</text>

    <text x="412" y="76" font-size="30" font-weight="700" fill="{NUM}" text-anchor="middle">{stars}</text>
    <text x="412" y="104" font-size="14" fill="{LABEL}" text-anchor="middle">Stars Earned</text>
    <text x="412" y="128" font-size="11" fill="{MUTED}" text-anchor="middle">Across repos</text>
  </g>
</svg>
'''


def main():
    try:
        data = fetch()
    except Exception as exc:  # noqa: BLE001
        print(f"stats fetch failed - leaving stats.svg unchanged: {exc}", file=sys.stderr)
        return 0

    print(f"commits={data['commits']} prs={data['prs']} issues={data['issues']} stars={data['stars']} repos={data['repos']}", file=sys.stderr)

    if data["commits"] == 0 and data["stars"] == 0:
        print("no data - leaving stats.svg unchanged", file=sys.stderr)
        return 0

    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(build_svg(data["commits"], data["prs"], data["issues"], data["stars"], data["repos"]))

    print(f"wrote {OUT}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

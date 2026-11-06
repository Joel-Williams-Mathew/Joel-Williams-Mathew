#!/usr/bin/env python3
"""Read streak.svg and publish the numbers as streak.json for the site."""
import json
import pathlib
import re
import sys


def main() -> int:
    svg_path = pathlib.Path("streak.svg")
    if not svg_path.exists():
        print("streak.svg not found", file=sys.stderr)
        return 0

    svg = svg_path.read_text(encoding="utf-8")
    nums = [
        int(v.strip())
        for v in re.findall(r">([^<>\n]+)</text>", svg)
        if v.strip().isdigit()
    ]

    if not nums:
        print("no numbers found in streak.svg", file=sys.stderr)
        return 0

    data = {
        "total": nums[0] if len(nums) > 0 else None,
        "current": nums[1] if len(nums) > 1 else None,
        "longest": nums[2] if len(nums) > 2 else None,
    }

    pathlib.Path("streak.json").write_text(
        json.dumps(data) + "\n", encoding="utf-8"
    )
    print("streak.json ->", data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

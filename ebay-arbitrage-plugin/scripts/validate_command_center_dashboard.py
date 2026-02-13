#!/usr/bin/env python3
"""Quick validator for command-center HTML contracts."""
from __future__ import annotations

import argparse
import pathlib
import re
import sys


TAB_ORDER = ["overview", "items", "listings", "bundles", "compliance", "cashflow", "scaling", "meta"]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Validate generated dashboard contract")
    p.add_argument("html_path", help="Path to generated HTML dashboard")
    p.add_argument("--expected-candidates", type=int, help="Expected candidate rows in overview table")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    path = pathlib.Path(args.html_path)
    if not path.exists():
        print(f"missing html: {path}")
        return 1

    text = path.read_text(encoding="utf-8", errors="replace")

    tabs = re.findall(r'data-tab="([a-z0-9_-]+)"', text)
    if tabs[: len(TAB_ORDER)] != TAB_ORDER:
        print(f"tab order mismatch: got={tabs[:len(TAB_ORDER)]} expected={TAB_ORDER}")
        return 1

    required_markers = [
        "Pinned Listings and Evidence",
        "Admin - Report Files",
        "candidate-row",
        "link-chip source",
        "evidence-thumb",
    ]
    for marker in required_markers:
        if marker not in text:
            print(f"missing marker: {marker}")
            return 1

    if args.expected_candidates is not None:
        overview_rows = len(re.findall(r"<tr class=\"candidate-row\"", text))
        if overview_rows < args.expected_candidates:
            print(f"candidate row count too low: {overview_rows} < {args.expected_candidates}")
            return 1

    print("dashboard contract: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

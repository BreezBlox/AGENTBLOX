#!/usr/bin/env python3
"""Prune reports/.runs and reports/.evidence to keep latest N runs."""
from __future__ import annotations

import argparse
import pathlib


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Prune run/evidence folders")
    p.add_argument("reports_dir", nargs="?", default="reports", help="Reports directory path")
    p.add_argument("--keep", type=int, default=3, help="Runs to keep (default: 3)")
    return p.parse_args()


def delete_tree(path: pathlib.Path) -> None:
    for f in path.rglob("*"):
        if f.is_file():
            f.unlink()
    for d in sorted([p for p in path.rglob("*") if p.is_dir()], reverse=True):
        d.rmdir()
    path.rmdir()


def prune(base: pathlib.Path, keep: int) -> int:
    if keep < 1 or not base.exists():
        return 0
    dirs = sorted([p for p in base.glob("*") if p.is_dir()], key=lambda p: p.stat().st_mtime, reverse=True)
    removed = 0
    for d in dirs[keep:]:
        delete_tree(d)
        removed += 1
    return removed


def main() -> int:
    args = parse_args()
    reports = pathlib.Path(args.reports_dir).resolve()
    runs = reports / ".runs"
    evidence = reports / ".evidence"
    removed_runs = prune(runs, args.keep)
    removed_evidence = prune(evidence, args.keep)
    print(f"removed runs: {removed_runs}")
    print(f"removed evidence: {removed_evidence}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

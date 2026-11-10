"""CLI: draft a patch for one issue, validate it in a temp copy,
write patch.diff + a report. Never applies anything to the repo.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
from .agent import run_issue
from .report import render_report, render_json

def main():
    parser = argparse.ArgumentParser(description="Issue-to-patch agent (draft only, human applies)")
    parser.add_argument("--issue", required=True, help="Path to an issue file (Markdown)")
    parser.add_argument("--repo", required=True, help="Path to the repo to patch")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Rule-based patcher, offline")
    parser.add_argument("--no-dry-run", dest="dry_run", action="store_false", help="Use the LLM path")
    parser.add_argument("--out-diff", default="patch.diff")
    parser.add_argument("--out-md", default="report.md")
    parser.add_argument("--out-json", default="")
    args = parser.parse_args()
    try:
        result = run_issue(args.issue, args.repo, dry_run=args.dry_run)
    except RuntimeError as exc:
        print(f"Error: {exc}")
        raise SystemExit(1)
    print(render_report(result))
    Path(args.out_md).write_text(render_report(result))
    if args.out_json:
        Path(args.out_json).write_text(render_json(result))
    if result["patch"]:
        Path(args.out_diff).write_text(result["patch"])
        print(f"\nWrote {args.out_diff} and {args.out_md}")
    else:
        print(f"\nNo patch written. Wrote {args.out_md}")

if __name__ == "__main__":
    main()

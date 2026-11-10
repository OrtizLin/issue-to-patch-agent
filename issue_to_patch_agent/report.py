"""Markdown + JSON report for one issue run."""
from __future__ import annotations
import json

def render_report(result):
    lines = [f"# Patch Report: {result['issue']}", ""]
    lines.append(f"Mode: {result['mode']} (prompt {result['prompt_version']})")
    lines.append(f"Status: {result['status']}")
    lines.append("")
    lines.append("## Located files")
    for item in result["located"]:
        lines.append(f"- `{item['path']}` (score {item['score']})")
    if result.get("evidence"):
        lines.append("")
        lines.append(f"Fix pattern evidence: `{result['evidence']}`")
    if result.get("summary"):
        lines.append("")
        lines.append(f"LLM summary: {result['summary']}")
    if result["validation"]:
        lines.append("")
        lines.append(f"Validation: {result['validation']}")
    if result["patch"]:
        lines.append("")
        lines.append("## Patch (validated in a temp copy; not applied)")
        lines.append("")
        lines.append("```diff")
        lines.append(result["patch"].rstrip())
        lines.append("```")
        lines.append("")
        lines.append("To apply after reviewing: `git apply patch.diff`")
    lines.append("")
    lines.append("> Human approval required before applying. This report is not an approval.")
    return "\n".join(lines)

def render_json(result):
    return json.dumps(result, indent=2, ensure_ascii=False)

"""Issue-to-patch loop: locate -> draft patch -> validate in temp copy -> report.
The tool never touches the real repo. The validated patch is written
to patch.diff for a human to review and apply with `git apply`.
"""
from __future__ import annotations
from pathlib import Path
from .locate import locate_files, LOCATE_THRESHOLD
from .patcher import draft_dry_run_patch, make_diff, validate_patch
from .prompts import PROMPT_VERSION, SYSTEM_PROMPT

def load_issue(issue_path):
    text = Path(issue_path).read_text()
    title = ""
    for line in text.splitlines():
        if line.startswith("Title:"):
            title = line[6:].strip()
            break
    return title or Path(issue_path).stem, text

def run_issue(issue_path, repo_dir, dry_run=True, top_k=3):
    title, issue_text = load_issue(issue_path)
    located = locate_files(repo_dir, issue_text, top_k=top_k)
    result = {
        "issue": title, "issue_path": str(issue_path), "repo": str(repo_dir),
        "located": [{"path": d["path"], "score": round(s, 4)} for d, s in located],
        "patch": None, "patch_valid": False, "validation": "",
        "mode": "dry-run" if dry_run else "llm",
        "prompt_version": PROMPT_VERSION,
        "status": "",
    }
    if not located or located[0][1] < LOCATE_THRESHOLD:
        result["status"] = "no patch: no file looks relevant to this issue"
        return result
    target = located[0][0]
    file_text = (Path(repo_dir) / target["path"]).read_text()
    allowed = [d["path"] for d, _ in located]
    if dry_run:
        new_text, evidence = draft_dry_run_patch(issue_text, target["path"], file_text)
        if new_text is None:
            result["status"] = "no patch: no supported dry-run fix pattern matches this issue (try LLM mode)"
            return result
        diff_text = make_diff(target["path"], file_text, new_text)
        result["evidence"] = evidence
    else:
        from .llm import complete_patch
        files_shown = "\n\n".join(
            f"--- {d['path']} ---\n{(Path(repo_dir) / d['path']).read_text()}"
            for d, _ in located)
        user_prompt = (
            f"Issue: {title}\n{issue_text}\n\n"
            f"Files (only touch these): {allowed}\n\n{files_shown}"
        )
        parsed = complete_patch(SYSTEM_PROMPT, user_prompt)
        diff_text = parsed["patch"]
        result["summary"] = parsed["summary"]
    ok, reason = validate_patch(repo_dir, diff_text, allowed)
    result["validation"] = reason
    if not ok:
        result["status"] = f"patch rejected: {reason}"
        return result
    result["patch"] = diff_text
    result["patch_valid"] = True
    result["status"] = "patch ready for human review (not applied to the repo)"
    return result

# Issue-to-Patch Agent

An AI agent that turns one issue into a validated patch draft.
It locates the relevant code, drafts a patch, checks the patch in
a temporary copy of the repo (applies cleanly, tests pass), and
stops. It never applies a patch to your real repo, never commits,
never merges, never pushes. A human reviews `patch.diff` and runs
`git apply patch.diff` if they agree.

This is portfolio project 3 for a Senior AI Agent Development
Engineer role, and the third in the same discipline as Projects
1 and 2: tools first, validate the output, measure it. Project 1
reviews code, Project 2 answers questions from documents, this
one changes code — so the validation bar is higher, because a
bad patch is worse than a bad comment.

## What it does

1. Read an issue file (Markdown: title, description, expected behaviour).
2. Locate the relevant files with TF-IDF over the repo's `.py` files.
   If no file looks relevant, it proposes no patch instead of guessing.
3. Draft a patch:
   - Dry-run (default, offline): three documented fix patterns,
     applied by exact string replacement (the anchor must occur
     exactly once). Anything else proposes no patch.
   - LLM mode (`--no-dry-run`): the model returns a unified diff
     as JSON, which is validated exactly like a dry-run patch.
4. Validate in temporary copies only: the diff must parse, only
   touch located files, pass `git apply --check`, and break no
   test that passed in an unpatched baseline copy. Pre-existing
   failures do not count against the patch.
5. Write `patch.diff` and `report.md`. Applying it to the real
   repo is the human's step.

## Quick start (no API key needed)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m issue_to_patch_agent.cli --issue examples/issues/issue-1-empty-average.md --repo examples/sample_repo
```

That produces a patch adding `if not numbers: return 0.0` to
`average()`, validated in a temp copy where the sample tests
pass. The sample repo itself is untouched.

```bash
# LLM path, key in your shell only, never in chat or a committed file:
export LLM_API_KEY=<redacted>
export LLM_MODEL="gemini-3-flash-preview"  # or a model you actually have access to
export LLM_BASE_URL="https://generativelanguage.googleapis.com/v1beta/openai"  # for a Google AI Studio key
python -m issue_to_patch_agent.cli --issue examples/issues/issue-1-empty-average.md --repo examples/sample_repo --no-dry-run
```

## Evaluation, not just a demo

```bash
python eval/run_eval.py
python -m pytest -q
```

`eval/cases.json` has 4 cases: 3 sample issues where a validated
patch must contain the expected change, and 1 issue (a new
feature, dark mode) where no patch must be proposed. The sample
tests fail on the buggy code and pass after the patch is applied
in the temp copy, so a passing eval means the patch really fixes
the issue, not just that a diff was produced. `eval/run_heldout.py`
scores a separate held-out set of 5 reworded issues, never used
for tuning: 5/5 on the first run. Validation compares the patched
temp copy against an unpatched baseline, so a patch must break no
previously passing test; pre-existing failures do not count
against it.

## What is intentionally not here yet

- Dry-run only knows three fix patterns. Real issues need the
  LLM path, and the LLM path needs a key.
- No held-out eval set yet. The 4 cases are the development set.
- No pull-request integration: the tool writes a patch file, it
  does not open a PR. (Project 1's PR-comment Action is the
  sibling piece for that half.)
- No auto-apply, no auto-commit, no auto-push, by design.

## Mapping to the target role

| Role requirement | Evidence in this repo |
| --- | --- |
| AI agents / workflow automation | Issue -> locate -> draft -> validate loop, human in the loop |
| LLM applications | OpenAI-compatible boundary, strict JSON patch contract |
| Prompt engineering | Versioned system prompt, minimal-change + scope rules |
| Tool calling | File search, git apply check, test runner as tools |
| Coding / testing / CI | Tests, eval, GitHub Actions |
| Developer productivity | A patch draft a developer can review in minutes, not a chat answer |

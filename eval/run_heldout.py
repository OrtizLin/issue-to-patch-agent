"""Score the held-out set (eval/heldout_cases.json).
Same scoring as eval/run_eval.py. Held-out rules (same as
Projects 1 and 2): these issues were written after the
development set and were never used for tuning. Run once and
report as-is; do not change code, rules, or prompts to make a
failing held-out case pass, and do not merge held-out cases
into the development set. This score is separate from the 4/4
development score.
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from issue_to_patch_agent.agent import run_issue

def main():
    root = Path(__file__).resolve().parent.parent
    cases = json.loads((root / "eval" / "heldout_cases.json").read_text())
    passed = 0
    for case in cases:
        issue = root / case["issue"]
        result = run_issue(str(issue), str(root / "examples" / "sample_repo"), dry_run=True)
        if case.get("expect_no_patch"):
            ok = result["patch"] is None
            detail = f"patch={'yes' if result['patch'] else 'no'}"
        else:
            ok = (
                result["patch"] is not None
                and result["patch_valid"]
                and case["expect_patch_contains"] in result["patch"]
            )
            detail = f"patch={'yes' if result['patch'] else 'no'} valid={result['patch_valid']}"
        print(f"{'PASS' if ok else 'FAIL'}: {issue.name} ({detail})")
        passed += ok
    print(f"Held-out: {passed}/{len(cases)} (separate from the development score)")
    raise SystemExit(0 if passed == len(cases) else 1)

if __name__ == "__main__":
    main()

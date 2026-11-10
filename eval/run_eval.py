"""Score the dry-run patcher on the sample issues.
Pass = a validated patch is produced, it contains the expected
change, and the repo tests pass after applying it in a temp copy
(the validator already checks the last two, so the check here is
that the right change is in the patch). A case that expects no
patch passes only when no patch is produced.
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from issue_to_patch_agent.agent import run_issue

def main():
    root = Path(__file__).resolve().parent.parent
    cases = json.loads((root / "eval" / "cases.json").read_text())
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
    print(f"{passed}/{len(cases)} cases passed")
    raise SystemExit(0 if passed == len(cases) else 1)

if __name__ == "__main__":
    main()

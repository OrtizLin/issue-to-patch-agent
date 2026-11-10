import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from issue_to_patch_agent.agent import run_issue
from issue_to_patch_agent.locate import locate_files
from issue_to_patch_agent.patcher import validate_patch, make_diff

ROOT = Path(__file__).resolve().parent.parent
REPO = ROOT / "examples" / "sample_repo"
ISSUES = ROOT / "examples" / "issues"

def test_issue_1_patch_contains_guard_and_validates():
    r = run_issue(str(ISSUES / "issue-1-empty-average.md"), str(REPO), dry_run=True)
    assert r["patch_valid"] and "if not numbers" in r["patch"]

def test_issue_2_patch_valid_despite_other_preexisting_failure():
    """Regression test (2026-11-10): a patch for the print issue must
    validate even though test_average_empty still fails in the same
    repo, because that failure is pre-existing, not caused by the
    patch. An earlier version rejected it, and an even earlier one
    only passed it by accident, reusing a patched module cached
    from the previous validation."""
    r = run_issue(str(ISSUES / "issue-2-print-greet.md"), str(REPO), dry_run=True)
    assert r["patch_valid"] and "logging.info" in r["patch"]

def test_issue_3_patch_valid():
    r = run_issue(str(ISSUES / "issue-3-bare-except.md"), str(REPO), dry_run=True)
    assert r["patch_valid"] and "except ValueError" in r["patch"]

def test_issue_4_proposes_no_patch():
    r = run_issue(str(ISSUES / "issue-4-dark-mode.md"), str(REPO), dry_run=True)
    assert r["patch"] is None

def test_locator_finds_calc_for_average_issue():
    top = locate_files(str(REPO), "average empty list ZeroDivisionError", top_k=1)
    assert top and top[0][0]["path"] == "calc.py"

def test_validation_rejects_patch_touching_unlocated_file():
    diff = make_diff("other.py", "x = 1\n", "x = 2\n")
    ok, reason = validate_patch(str(REPO), diff, ["calc.py"])
    assert not ok and "outside the located set" in reason

def test_validation_rejects_garbage_diff():
    ok, reason = validate_patch(str(REPO), "not a diff at all", ["calc.py"])
    assert not ok

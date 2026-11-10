"""Dry-run patcher and patch validation.

Dry-run supports exactly three documented fix patterns, applied
by exact string replacement (the anchor must occur exactly once,
or no patch is proposed). Anything else needs the LLM path, and
even the LLM path is only a draft until it passes validation.

Validation (in temporary copies of the repo, never the real one):
1. The diff parses as a unified diff and only touches files the
   locator returned.
2. `git apply --check` accepts it in the temp copy.
3. The repo's tests run in an unpatched temp copy (the baseline)
   and in a patched temp copy. The patch is accepted only if it
   breaks no test that passed in the baseline. Pre-existing
   failures do not count against the patch: the sample repo has
   three independent bugs, so a patch for one of them must not
   be rejected because another bug's test still fails. (That is
   also why the test runner clears cached repo modules between
   runs: without that, a patched module from one validation
   leaked into the next and made a later patch look passing.)
If any step fails, the patch is rejected with the reason, and no
patch.diff is written. A validated patch still needs a human to
run `git apply patch.diff` on the real repo.
"""
from __future__ import annotations
import difflib, re, shutil, subprocess, sys, tempfile
from pathlib import Path

# Each pattern: (keywords in the issue, anchor, replacement, evidence string)
PATTERNS = [
    (
        ("zerodivisionerror", "empty"),
        "def average(numbers):\n    return sum(numbers) / len(numbers)",
        "def average(numbers):\n    if not numbers:\n        return 0.0\n    return sum(numbers) / len(numbers)",
        "if not numbers: return 0.0",
    ),
    (
        ("print", "logging"),
        '    print("hello " + name)',
        '    logging.info("hello " + name)',
        "logging.info",
    ),
    (
        ("bare", "except"),
        "    except:\n        return 0",
        "    except ValueError:\n        return 0",
        "except ValueError",
    ),
]

def _add_import_after_docstring(text, import_line):
    """Add an import after a leading module docstring, not before it.
    A string literal before the docstring would stop being the
    module docstring."""
    if text.startswith('"""'):
        end = text.find('"""', 3)
        if end >= 0:
            cut = end + 3
            return text[:cut] + "\n\n" + import_line + text[cut:]
    return import_line + "\n" + text

def draft_dry_run_patch(issue_text, file_path, file_text):
    """Return (new_text, pattern_evidence) or (None, None)."""
    lowered = issue_text.lower()
    for keywords, anchor, replacement, evidence in PATTERNS:
        if not any(k in lowered for k in keywords):
            continue
        if file_text.count(anchor) != 1:
            continue
        new_text = file_text.replace(anchor, replacement)
        if "logging.info" in replacement and "import logging" not in new_text:
            new_text = _add_import_after_docstring(new_text, "import logging")
        return new_text, evidence
    return None, None

def make_diff(rel_path, old_text, new_text):
    lines = difflib.unified_diff(
        old_text.splitlines(keepends=True),
        new_text.splitlines(keepends=True),
        fromfile=f"a/{rel_path}", tofile=f"b/{rel_path}",
    )
    return "".join(lines)

def _clear_repo_modules(repo_tmp):
    """Drop cached modules loaded from a temp copy, so the next
    validation loads the repo files from its own temp copy instead
    of reusing a patched module cached from the previous one."""
    tmp = str(repo_tmp)
    for name in list(sys.modules):
        mod = sys.modules.get(name)
        path = getattr(mod, "__file__", "") or ""
        if path.startswith(tmp):
            del sys.modules[name]

def _run_tests(repo_tmp, test_files):
    """Run test_*.py files with the standard library only.
    Returns a list of failure descriptions (empty = all passed).
    Each test module is loaded fresh; test_* callables are run in
    definition order. A module that cannot be imported counts as
    a failure, not a silent skip."""
    import contextlib, importlib.util, io
    failures = []
    for path in sorted(test_files):
        _clear_repo_modules(repo_tmp)
        spec = importlib.util.spec_from_file_location(path.stem, path)
        if spec is None or spec.loader is None:
            failures.append(f"{path.name}: could not load")
            continue
        module = importlib.util.module_from_spec(spec)
        sys.path.insert(0, str(repo_tmp))
        try:
            spec.loader.exec_module(module)
        except Exception as exc:  # noqa: BLE001 - any import error is a failure
            failures.append(f"{path.name}: import failed: {exc}")
            continue
        finally:
            sys.path.remove(str(repo_tmp))
        for name in sorted(dir(module)):
            if not name.startswith("test_"):
                continue
            fn = getattr(module, name)
            if not callable(fn):
                continue
            try:
                with contextlib.redirect_stdout(io.StringIO()):
                    fn()
            except Exception as exc:  # noqa: BLE001 - any test error is a failure
                failures.append(f"{path.name}::{name}: {type(exc).__name__}: {exc}")
        _clear_repo_modules(repo_tmp)
    return failures

def diff_files(diff_text):
    """File paths a unified diff touches (the b/ side)."""
    return re.findall(r"^\+\+\+ b/(.+)$", diff_text, flags=re.M)

def validate_patch(repo_dir, diff_text, allowed_paths, timeout=120):
    """Returns (ok, reason). Validates in a temp copy only."""
    if not diff_text.strip():
        return False, "empty diff"
    touched = diff_files(diff_text)
    if not touched:
        return False, "diff touches no file (not a unified diff?)"
    extra = [p for p in touched if p not in allowed_paths]
    if extra:
        return False, f"patch touches files outside the located set: {extra}"
    base = Path(tempfile.mkdtemp(prefix="issue-patch-base-"))
    tmp = Path(tempfile.mkdtemp(prefix="issue-patch-"))
    try:
        ignore = shutil.ignore_patterns(".venv", "__pycache__", ".git")
        shutil.copytree(repo_dir, base, dirs_exist_ok=True, ignore=ignore)
        shutil.copytree(repo_dir, tmp, dirs_exist_ok=True, ignore=ignore)
        (tmp / "patch.diff").write_text(diff_text)
        check = subprocess.run(
            ["git", "apply", "--check", "patch.diff"],
            cwd=tmp, capture_output=True, text=True, timeout=timeout)
        if check.returncode != 0:
            return False, f"git apply --check failed: {check.stderr.strip()}"
        applied = subprocess.run(
            ["git", "apply", "patch.diff"],
            cwd=tmp, capture_output=True, text=True, timeout=timeout)
        if applied.returncode != 0:
            return False, f"git apply failed: {applied.stderr.strip()}"
        # Stdlib-only test runner, so validation works on any machine
        # with Python alone. Compare against the unpatched baseline:
        # a patch must break no previously passing test.
        base_files = [p for p in Path(base).rglob("test_*.py")]
        patched_files = [p for p in Path(tmp).rglob("test_*.py")]
        base_failures = set(_run_tests(base, base_files)) if base_files else set()
        patched_failures = set(_run_tests(tmp, patched_files)) if patched_files else set()
        new_failures = patched_failures - base_failures
        if new_failures:
            return False, "patch breaks previously passing tests: " + "; ".join(sorted(new_failures)[:3])
        if patched_failures:
            return True, (
                "patch applies cleanly and breaks no previously passing test; "
                f"{len(patched_failures)} pre-existing failure(s) remain: "
                + "; ".join(sorted(patched_failures)[:2])
            )
        return True, "patch applies cleanly and tests pass in a temp copy"
    finally:
        shutil.rmtree(base, ignore_errors=True)
        shutil.rmtree(tmp, ignore_errors=True)

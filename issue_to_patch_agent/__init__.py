"""Issue-to-patch agent: read an issue, locate the code, draft a patch,
validate it in a temporary copy, and stop. It never applies a patch
to your real repo and never commits, merges, or pushes. A human
reviews patch.diff and applies it with `git apply` if they agree.
"""

"""Locate the files an issue is about. Small TF-IDF search over the
repo's .py files, same idea as Projects 1 and 2: the issue text is
the query, each file is a document, top-k by cosine similarity.
A best score below LOCATE_THRESHOLD means "no file looks relevant"
and the agent proposes no patch instead of guessing.
"""
from __future__ import annotations
import math, re
from collections import Counter
from pathlib import Path

LOCATE_THRESHOLD = 0.05
STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "to", "in", "on", "for", "with",
    "how", "what", "is", "are", "was", "were", "do", "does", "did",
    "it", "its", "this", "that", "should", "when", "add", "file",
}

def _tokens(text):
    return [t for t in re.findall(r"[a-z0-9_]+", text.lower()) if t not in STOPWORDS]

def list_python_files(repo_dir):
    root = Path(repo_dir)
    files = []
    for path in sorted(root.rglob("*.py")):
        if ".venv" in path.parts or "__pycache__" in path.parts:
            continue
        if path.name.startswith("test_"):
            continue
        files.append(path)
    return files

def locate_files(repo_dir, issue_text, top_k=3):
    files = list_python_files(repo_dir)
    docs = []
    for path in files:
        try:
            text = path.read_text()
        except OSError:
            continue
        docs.append({"path": str(path.relative_to(repo_dir)), "text": text})
    if not docs or not issue_text.strip():
        return []
    qtokens = _tokens(issue_text)
    if not qtokens:
        return []
    df = Counter()
    doc_tokens = []
    for d in docs:
        toks = _tokens(d["text"])
        doc_tokens.append(Counter(toks))
        for t in set(toks):
            df[t] += 1
    n = len(docs)
    scored = []
    for d, counts in zip(docs, doc_tokens):
        total = sum(counts.values()) or 1
        score = 0.0
        for t in qtokens:
            if counts.get(t):
                idf = math.log((n + 1) / (df[t] + 1)) + 1.0
                score += (counts[t] / total) * idf
        scored.append((d, score))
    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:top_k]

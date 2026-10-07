#!/usr/bin/env python3
"""Word error rate and the gap list between a reference passage and a transcription.
Usage: uv run tools/wer.py ref.txt hyp.txt   (or pass the two texts as arguments)"""
import re, sys

def norm(t): return re.sub(r"[^\w\s]", " ", t.lower()).split()

def score(ref, hyp):
    r, h = norm(ref), norm(hyp); n, m = len(r), len(h)
    D = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1): D[i][0] = i
    for j in range(m + 1): D[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            D[i][j] = min(D[i - 1][j] + 1, D[i][j - 1] + 1, D[i - 1][j - 1] + (r[i - 1] != h[j - 1]))
    i, j, gaps = n, m, []
    while i > 0 or j > 0:                                   # walk back: collect what was heard differently
        if i > 0 and j > 0 and D[i][j] == D[i - 1][j - 1] + (r[i - 1] != h[j - 1]):
            if r[i - 1] != h[j - 1]: gaps.append((r[i - 1], h[j - 1]))
            i, j = i - 1, j - 1
        elif i > 0 and D[i][j] == D[i - 1][j] + 1: gaps.append((r[i - 1], "")); i -= 1
        else: gaps.append(("", h[j - 1])); j -= 1
    gaps.reverse(); e = D[n][m]
    return {"n_ref": n, "errors": e, "wer": e / n if n else 0.0, "gaps": gaps}

if __name__ == "__main__":
    a, b = sys.argv[1], sys.argv[2]
    ref = open(a).read() if a.endswith(".txt") else a; hyp = open(b).read() if b.endswith(".txt") else b
    s = score(ref, hyp)
    print(f"WER {s['wer']:.1%}  ({s['errors']} errors / {s['n_ref']} words)")
    for g in s["gaps"]: print(f"  {g[0] or '∅':20} → {g[1] or '∅'}")

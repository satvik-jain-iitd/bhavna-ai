#!/usr/bin/env python3
"""Reads stats.jsonl and prints release-to-text p50/p90 per length bucket, with the parts that explain it.
Usage: uv run tools/report.py [stats.jsonl] [--since YYYY-MM-DD] [--split YYYY-MM-DD] [--profiles] [--left]"""
import json, sys
from pathlib import Path

BUCKETS = [("<5s", 0, 5), ("5-15s", 5, 15), ("15-30s", 15, 30), ("30s+", 30, 1e9)]

def pct(xs, q):
    xs = sorted(xs); return xs[min(len(xs) - 1, int(round(q * (len(xs) - 1))))] if xs else None
def p50(xs): return pct(xs, 0.5)
def p90(xs): return pct(xs, 0.9)

def summarize(rows):
    out = {}
    for name, lo, hi in BUCKETS:
        rs = [r for r in rows if lo <= r.get("audio_s", 0) < hi and "release_to_text_ms" in r]
        if not rs: continue
        g = lambda k: [r.get(k, 0) for r in rs]
        out[name] = {"n": len(rs), "p50": p50(g("release_to_text_ms")), "p90": p90(g("release_to_text_ms")),
                     "wait_p50": p50(g("wait_ms")), "final_p50": p50(g("final_asr_ms")), "insert_p50": p50(g("insert_ms")),
                     "rtf_p50": p50(g("rtf")) if any("rtf" in r for r in rs) else None,
                     "forced": sum(g("forced_cuts")), "pause": sum(g("pause_cuts")), "errors": sum(g("errors"))}
    return out

def left_table(history, points=(2, 5, 10, 20, 40), q=0.5):
    """P3: expected_left at a few talk lengths. Run with: uv run --project macos tools/report.py --left"""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "macos"))
    from dictate import expected_left
    return [(e, expected_left(e, history, q)) for e in points]

def by_profile(rows):
    out = {}
    for r in rows: out.setdefault(r.get("profile", "lean"), []).append(r)   # rows before ADR-015 have no profile: lean
    return out

def model_mix(rows):
    out = {}
    for r in rows:
        for m, n in r.get("models", {}).items(): out[m] = out.get(m, 0) + n
    return out

def split(rows, day): return [r for r in rows if r["ts"][:10] < day], [r for r in rows if r["ts"][:10] >= day]

def show(title, rows):
    print(f"## {title}: {len(rows)} dictations")
    print(f"{'bucket':8} {'n':>3} {'p50':>6} {'p90':>6} | {'wait':>5} {'final':>6} {'insert':>6} {'rtf':>5} | pause forced err")
    for b, s in summarize(rows).items():
        print(f"{b:8} {s['n']:>3} {s['p50']:>6} {s['p90']:>6} | {s['wait_p50']:>5} {s['final_p50']:>6} {s['insert_p50']:>6} {str(s['rtf_p50']):>5} | {s['pause']:>5} {s['forced']:>6} {s['errors']:>3}")

if __name__ == "__main__":
    args = sys.argv[1:]; path = Path(args[0]) if args and not args[0].startswith("--") else Path(__file__).resolve().parents[1] / "stats.jsonl"
    rows = [json.loads(l) for l in open(path) if l.strip()]
    if "--profiles" in args:
        for prof, rs in by_profile(rows).items(): show(f"{prof} (models {model_mix(rs) or 'apex only'})", rs)
        sys.exit()
    if "--left" in args:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "macos"))
        import dictate
        hist = dictate.talk_history(path)   # the same rule pick() sees: under 30 rows = no history
        print(f"## expected talk time left, from {len(hist)} dictations (0 = too few, fallback)")
        for (e, med), (_, careful) in zip(left_table(hist), left_table(hist, q=dictate.SLACK_Q)):
            print(f"talked {e:>2} s -> median {med:5.1f} s | careful (q={dictate.SLACK_Q}, what pick uses) {careful:5.1f} s")
        sys.exit()
    if "--since" in args: rows = [r for r in rows if r["ts"][:10] >= args[args.index("--since") + 1]]
    if "--split" in args:
        before, after = split(rows, args[args.index("--split") + 1]); show("before", before); show("after", after)
    else:
        for day in sorted({r["ts"][:10] for r in rows}): show(day, [r for r in rows if r["ts"].startswith(day)])

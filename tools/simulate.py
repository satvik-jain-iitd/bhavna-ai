#!/usr/bin/env python3
"""P2 T2.7a: replay the logged chunk timing through a model policy with NO model run (one FIFO worker).
Predicts release-to-text for `lean` (Apex only) and `cascade` (ADR-015) from the 592 logged dictations.
RTF values are guesses until T2.4 measures them, so it sweeps three scenarios. A prediction, not a result.
Run: uv run --project macos tools/simulate.py [log_dir]"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "macos"))
POSTROLL_S, INSERT_S = 0.3, 0.05


def simulate(chunks, audio_s, decide, cost):
    """Chunk i is cut at end_s. The worker takes chunks in order. decide(len_s, queued_s, e, released) -> model name.
    cost(chunk, model) -> decode seconds. Release-to-text = wait for the last chunk after the audio ends + postroll + insert."""
    free, finish = 0.0, 0.0
    for i, c in enumerate(chunks):
        start = max(c["end_s"], free)
        n = c["end_s"] - c["start_s"]
        queued = sum(x["end_s"] - x["start_s"] for x in chunks[i + 1:] if x["end_s"] <= start)
        m = decide(n, queued, start, start >= audio_s)
        finish = free = start + cost(c, m)
    return max(finish - audio_s, 0.0) + POSTROLL_S + INSERT_S


def pct(xs, q):
    xs = sorted(xs); return xs[min(len(xs) - 1, int(round(q * (len(xs) - 1))))]


SCENARIOS = {   # decode time relative to Apex on the same chunk: the ratios T2.4 will measure
    "pessimistic (swift .3x, prime 3x)": {"swift": 0.3, "apex": 1.0, "prime": 3.0},
    "likely (swift .2x, prime 2x)": {"swift": 0.2, "apex": 1.0, "prime": 2.0},
    "optimistic (swift .15x, prime 1.2x)": {"swift": 0.15, "apex": 1.0, "prime": 1.2},
}


def main():
    import statistics, dictate as d
    logs = [json.load(open(f)) for f in sorted(Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "log").glob("*.json"))]
    logs = [l for l in logs if l.get("chunks_detail") and "release_to_text_ms" in l]
    hist = d.talk_history()
    apex_rtf = statistics.median(c["ms"] / 1000 / (c["end_s"] - c["start_s"]) for l in logs for c in l["chunks_detail"] if c["end_s"] - c["start_s"] > 0.5)
    print(f"{len(logs)} logged dictations, talk history {len(hist)} rows, Apex chunk RTF p50 {apex_rtf:.2f}. Release-to-text, seconds.\n")
    print(f"{'policy':46} {'p50':>6} {'p90':>6}")
    real = [l["release_to_text_ms"] / 1000 for l in logs]
    print(f"{'lean, measured':46} {pct(real, .5):>6.2f} {pct(real, .9):>6.2f}")
    sim_lean = lambda ratios: [simulate(l["chunks_detail"], l["audio_s"], lambda n, q, e, rel: "apex", lambda c, m: c["ms"] / 1000 * ratios[m]) for l in logs]
    r = sim_lean(SCENARIOS["likely (swift .2x, prime 2x)"])
    print(f"{'lean, simulated (should match measured)':46} {pct(r, .5):>6.2f} {pct(r, .9):>6.2f}")
    for name, ratios in SCENARIOS.items():
        rtf = {m: apex_rtf * x for m, x in ratios.items()}
        mix = {"prime": 0.0, "apex": 0.0, "swift": 0.0}
        def cas(n, q, e, rel):
            m = d.pick_last(n, rtf) if rel else d.pick(n, q * rtf["apex"], e, hist, 4000, rtf)[0]
            mix[m] += n; return m
        rel = [simulate(l["chunks_detail"], l["audio_s"], cas, lambda c, m: c["ms"] / 1000 * ratios[m]) for l in logs]
        tot = sum(mix.values())
        print(f"{'cascade, ' + name:46} {pct(rel, .5):>6.2f} {pct(rel, .9):>6.2f}   audio by model: " + " ".join(f"{k} {100 * v / tot:.0f}%" for k, v in mix.items()))


if __name__ == "__main__":
    main()

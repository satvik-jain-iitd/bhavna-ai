#!/usr/bin/env python3
"""S1.2 bench: latency and language-ID per fixture clip, on the models in models/.
Run:  uv run --project macos --extra bench tools/bench.py
Writes a table to stdout and appends it to docs/research/experiments.md.
"""
import json, os, statistics, subprocess, sys, time, wave
from datetime import date
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
M, FX = ROOT / "models", ROOT / "tests" / "fixtures"
RUNS = int(os.environ.get("RUNS", 5))
ONLY = os.environ.get("ONLY", "lid,parakeet,apex").split(",")   # isolate one model on a tight machine
CLIPS = os.environ.get("CLIPS", "")                                 # substring filter on fixture names

def wav(p):
    with wave.open(str(p)) as w:
        assert w.getframerate() == 16000 and w.getnchannels() == 1, p
        return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768

def timed(fn):
    ts = []
    for _ in range(RUNS):
        t = time.perf_counter(); out = fn(); ts.append((time.perf_counter() - t) * 1000)
    ts.sort(); return out, ts[len(ts) // 2], ts[int(len(ts) * 0.9) - 1 if len(ts) > 1 else 0]

def main():
    import mlx.core as mx, mlx_whisper
    from mlx_whisper.load_models import load_model
    from mlx_whisper.audio import log_mel_spectrogram, pad_or_trim, N_FRAMES, N_SAMPLES
    from mlx_whisper.decoding import detect_language
    from parakeet_mlx import from_pretrained
    from parakeet_mlx.audio import get_logmel

    silence = np.zeros(16000, np.float32)
    tiny = load_model(str(M / "tiny-mlx"), dtype=mx.float16) if "lid" in ONLY else None
    pk = from_pretrained(str(M / "parakeet-v2-mlx")) if "parakeet" in ONLY else None
    apex = str(M / "apex-mlx-q8")
    if "apex" in ONLY: mlx_whisper.transcribe(silence, path_or_hf_repo=apex, language="en", temperature=0.0, fp16=True)  # warm
    nan = lambda *_: {"en": float("nan")}

    def lid(a):
        mel = pad_or_trim(log_mel_spectrogram(a, n_mels=tiny.dims.n_mels, padding=N_SAMPLES), N_FRAMES, axis=-2).astype(mx.float16)
        _, probs = detect_language(tiny, mel); return probs[0] if isinstance(probs, list) else probs
    def para(a):
        return pk.generate(get_logmel(mx.array(a), pk.preprocessor_config))[0].text
    def apx(a):
        return mlx_whisper.transcribe(a, path_or_hf_repo=apex, language="en", temperature=0.0, fp16=True,
                                      condition_on_previous_text=False, no_speech_threshold=None,
                                      compression_ratio_threshold=None, logprob_threshold=None)["text"].strip()
    rows = []
    for p in sorted(FX.glob("*.wav")):
        a = wav(p); secs = len(a) / 16000
        if CLIPS and CLIPS not in p.stem: continue
        probs, l50, l90 = timed(lambda: lid(a)) if tiny else (nan(), float("nan"), float("nan")); pen = probs.get("en", 0.0)
        pt, p50, p90 = timed(lambda: para(a)) if pk else ("-", float("nan"), float("nan"))
        at, a50, a90 = timed(lambda: apx(a)) if "apex" in ONLY else ("-", float("nan"), float("nan"))
        rows.append((p.stem, secs, pen, l50, p50, p90, a50, a90, pt, at))
        print(f"{p.stem:14} {secs:4.1f}s  p(en)={pen:.2f} lid {l50:4.0f}ms | parakeet p50 {p50:5.0f} p90 {p90:5.0f} | apex p50 {a50:5.0f} p90 {a90:5.0f}\n   PK: {pt}\n   AX: {at}", flush=True)
    tbl = ["", f"## Bench run {date.today()} (M1 8 GB, RUNS={RUNS}, ONLY={ONLY}, tiny fp16 / parakeet bf16 / apex q8; swap used {subprocess.run(['sysctl','-n','vm.swapusage'],capture_output=True,text=True).stdout.split()[5]})", "",
           "| clip | s | p(en) | lid ms | parakeet p50 | p90 | apex p50 | p90 |", "|---|---|---|---|---|---|---|---|"]
    tbl += [f"| {r[0]} | {r[1]:.1f} | {r[2]:.2f} | {r[3]:.0f} | {r[4]:.0f} | {r[5]:.0f} | {r[6]:.0f} | {r[7]:.0f} |" for r in rows]
    with open(ROOT / "docs/research/experiments.md", "a") as f: f.write("\n".join(tbl) + "\n")
    assert rows, "no fixtures"
    for r in rows:
        assert not any("ऀ" <= c <= "ॿ" for c in r[9]), f"Devanagari in Apex output for {r[0]}"
    print(f"mlx peak memory {mx.get_peak_memory() / 1e9:.2f} GB")
    print("ok: no Devanagari in any Apex output")

if __name__ == "__main__":
    main()

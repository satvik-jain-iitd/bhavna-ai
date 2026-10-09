#!/usr/bin/env python3
"""H3 follow-up: Apex latency per backend and encoder window. Run: uv run --project macos --with pywhispercpp tools/bench_apex.py"""
import os, sys, time, wave
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]; M, FX = ROOT / "models", ROOT / "tests" / "fixtures"
CLIPS = sorted(p.stem for p in FX.glob("*.wav"))
RUNS = int(os.environ.get("RUNS", 3))

def wav(p):
    with wave.open(str(p)) as w: return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768

def timed(fn):
    ts = []
    for _ in range(RUNS): t = time.perf_counter(); out = fn(); ts.append((time.perf_counter() - t) * 1000)
    return out, sorted(ts)[len(ts) // 2]

def mlx_variant(folder, window_s):
    import mlx.core as mx
    from mlx_whisper.load_models import load_model
    from mlx_whisper.audio import log_mel_spectrogram, pad_or_trim
    from mlx_whisper.decoding import decode, DecodingOptions
    from mlx_whisper import whisper as W
    orig = W.AudioEncoder.__call__
    def call(self, x):  # ponytail: slice the sinusoid table to the window; whisper.cpp's audio_ctx does the same
        import mlx.nn as nn
        x = nn.gelu(self.conv1(x)); x = nn.gelu(self.conv2(x))
        x = x + self._positional_embedding[: x.shape[1]]
        for block in self.blocks: x, _, _ = block(x)
        return self.ln_post(x)
    W.AudioEncoder.__call__ = call
    model = load_model(str(folder), dtype=mx.float16)
    frames = window_s * 100
    opts = DecodingOptions(language="en", task="transcribe", without_timestamps=True, temperature=0.0, fp16=True)
    def run(a):
        pad = max(0, window_s * 16000 - len(a))  # pad the audio, not the mel: log-mel normalises over the whole window
        mel = pad_or_trim(log_mel_spectrogram(a, n_mels=model.dims.n_mels, padding=pad), frames, axis=-2).astype(mx.float16)
        return decode(model, mel, opts).text.strip()
    run(np.zeros(16000, np.float32))
    yield run
    W.AudioEncoder.__call__ = orig

def cpp_variant(window_s):
    from pywhispercpp.model import Model
    m = Model(str(M / "ggml/ggml-apex-hinglish-q8_0.bin"), n_threads=4, print_progress=False, print_realtime=False)
    def run(a):
        segs = m.transcribe(a, language="en", audio_ctx=window_s * 50, single_segment=True, no_timestamps=True)
        return " ".join(s.text for s in segs).strip()
    run(np.zeros(16000, np.float32)); yield run

WINDOWS = [int(w) for w in os.environ.get("WINDOWS", "30,15,10,5").split(",")]
variants = [(f"mlx-q8-{w}s", lambda w=w: mlx_variant(M / "apex-mlx-q8", w)) for w in WINDOWS]
try:
    import pywhispercpp  # noqa
    variants += [(f"cpp-q8-{w}s", lambda w=w: cpp_variant(w)) for w in WINDOWS]
except ImportError: print("pywhispercpp not installed; skipping whisper.cpp variants")
only = os.environ.get("ONLY"); ref = {}
for name, mk in variants:
    if only and only not in name: continue
    try:
        gen = mk(); run = next(gen); tot, diff = 0.0, 0
        for c in CLIPS:
            a = wav(FX / f"{c}.wav"); text, ms = timed(lambda: run(a)); tot += ms
            ref.setdefault(c, text); flag = "" if text == ref[c] else "  <- differs from 30 s"; diff += bool(flag)
            print(f"{name:12} {c:28} {len(a)/16000:4.1f}s  {ms:6.0f} ms  {text}{flag}", flush=True)
        print(f"## {name}: mean {tot/len(CLIPS):.0f} ms, {diff}/{len(CLIPS)} clips differ from the 30 s text", flush=True)
        for _ in gen: pass
    except Exception as e: print(f"{name}: FAILED {type(e).__name__}: {e}", flush=True)

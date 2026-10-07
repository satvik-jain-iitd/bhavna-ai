"""Bug #94: a quiet mic (speech rms ~0.008, room ~0.0025) must still be chunked at pauses and never trimmed inside speech."""
import sys, wave
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "macos"))
import dictate as d

SR, BLOCK = 16000, 1600
rng = np.random.default_rng(1)
def quiet_speech(sec):
    t = np.arange(int(sec * SR)) / SR
    return (rng.standard_normal(len(t)) * 0.012 * (0.55 + 0.45 * np.sin(2 * np.pi * 3 * t))).astype(np.float32)
def room(sec): return (rng.standard_normal(int(sec * SR)) * 0.0025).astype(np.float32)
def feed(ch, a):
    if not ch.band_log: a = np.concatenate([room(0.5), a])
    out = []
    for i in range(0, len(a) - len(a) % BLOCK, BLOCK): out += ch.push(a[i:i + BLOCK])
    return out


def test_quiet_mic_is_detected_and_cut_at_pauses():
    ch = d.Chunker(); a = np.concatenate([room(0.5), quiet_speech(5.0), room(0.4), quiet_speech(5.0), room(0.4), quiet_speech(2.0)])
    out = feed(ch, a); last = ch.flush(final=True)
    assert len(out) == 2 and all(b["kind"] == "pause" for b in ch.bounds[:2])
    assert sum(b["speech_s"] for b in ch.bounds) >= 7.0            # syllable dips count as quiet; most of 12 s is speech
    assert last is not None and ch.bounds[-1]["end_s"] >= len(a) / SR - 0.2   # final keeps its tail


def test_final_chunk_is_never_trimmed_at_the_end():
    ch = d.Chunker(); a = np.concatenate([room(0.5), quiet_speech(3.0), room(0.3), quiet_speech(1.0)])
    out = feed(ch, a); last = ch.flush(final=True)
    assert np.array_equal(last[-BLOCK:], a[-BLOCK:])                                 # tail untouched
    assert sum(len(c) for c in out) + len(last) >= len(a) + 0.5 * SR - 1.1 * SR        # only leading room (≤ 1 s) may go


LOG = Path(__file__).resolve().parents[1] / "log"
import pytest


@pytest.mark.parametrize("stem,min_pauses,min_speech", [("20261007-175831", 5, 25), ("20261007-182007", 5, 40), ("20261007-190404", 5, 20)])
def test_owner_recording_regression(stem, min_pauses, min_speech):
    """#94 and #99: the owner's own recordings (outside git): quiet built-in mic (175831), clean (182007), noisy input (190404)."""
    f = LOG / f"{stem}.wav"
    if not f.exists(): pytest.skip("owner recording not on this machine")
    w = wave.open(str(f)); a = np.frombuffer(w.readframes(10**9), np.int16).astype(np.float32) / 32768
    ch = d.Chunker(); out = feed(ch, a); last = ch.flush(final=True)
    kinds = [b["kind"] for b in ch.bounds]
    assert kinds.count("pause") >= min_pauses, kinds
    assert sum(b["speech_s"] for b in ch.bounds) >= min_speech
    assert ch.bounds[-1]["end_s"] >= len(a) / 16000 - 0.3                 # tail kept
    assert sum(len(c) for c in out) + len(last) >= 0.9 * len(a)            # nothing much trimmed

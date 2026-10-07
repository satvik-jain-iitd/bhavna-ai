"""E2 scenarios: ring buffer with pre-roll (S2.1), short clips dropped (S2.2), stats row (S2.6),
Rosetta guard (S2.4). Pure logic, no model, no mic."""
import json, sys
from pathlib import Path
import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "macos"))
import dictate as d

SR = 16000
BLOCK = 1600  # 100 ms


def feed(ring, seconds, start_value):
    """Push `seconds` of blocks whose samples are a ramp, so slices are identifiable."""
    v = start_value
    for _ in range(int(seconds * SR / BLOCK)):
        ring.push(np.full(BLOCK, v, np.float32)); v += 1
    return v


def test_s2_1_clip_includes_preroll():
    ring = d.Ring(preroll_s=0.5, sr=SR)
    v = feed(ring, 2.0, 0)            # mic open 2 s before the key
    ring.start()                      # key down at t=2.0
    feed(ring, 2.0, v)                # held 2 s
    clip = ring.stop()                # key up at t=4.0
    assert abs(len(clip) / SR - 2.5) <= BLOCK / SR
    # first 500 ms are the five blocks pushed just before start (values 15..19)
    assert clip[0] == 15 and clip[int(0.5 * SR) - 1] == 19
    assert clip[int(0.5 * SR)] == v   # then the first block after the key


def test_s2_1_preroll_does_not_grow_without_bound():
    ring = d.Ring(preroll_s=0.5, sr=SR)
    feed(ring, 30.0, 0)
    assert sum(len(b) for b in ring.pre) <= int(0.5 * SR) + BLOCK


def test_s2_2_short_clip_is_dropped():
    assert d.too_short(np.zeros(int(0.2 * SR), np.float32))
    assert not d.too_short(np.zeros(int(0.3 * SR), np.float32))


def test_s2_6_stats_row_written(tmp_path):
    p = tmp_path / "stats.jsonl"
    d.stats(p, route="en", lid_ms=48, asr_ms=412, insert_ms=31, text="send the deck to rahul", audio_s=2.5)
    row = json.loads(p.read_text().splitlines()[-1])
    assert row["route"] == "en" and row["words"] == 5 and row["audio_s"] == 2.5
    assert "text" not in row and "ts" in row


def test_s2_4_rosetta_guard(monkeypatch):
    monkeypatch.setattr(d.platform, "machine", lambda: "x86_64")
    assert not d.native()
    monkeypatch.setattr(d.platform, "machine", lambda: "arm64")
    monkeypatch.setattr(d, "translated", lambda: False)
    assert d.native()

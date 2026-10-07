"""Bug #56: clips over 30 s must be split at quiet points, nothing dropped. Post-roll constant exists."""
import sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "macos"))
import dictate as d

SR = 16000


def test_short_clip_is_one_piece():
    a = np.ones(20 * SR, np.float32)
    assert [len(p) for p in d.pieces(a)] == [20 * SR]


def test_long_clip_splits_at_the_quiet_point_and_keeps_everything():
    a = np.ones(70 * SR, np.float32) * 0.5
    a[int(29.0 * SR): int(29.2 * SR)] = 0.0      # a pause just before the 30 s boundary
    a[int(57.0 * SR): int(57.2 * SR)] = 0.0
    ps = d.pieces(a)
    assert sum(len(p) for p in ps) == len(a)
    assert all(len(p) <= 30 * SR for p in ps)
    assert 29.0 <= len(ps[0]) / SR <= 29.2            # cut inside the pause, not at a hard 30.0


def test_postroll_constant():
    assert 0.1 <= d.POSTROLL_S <= 0.5

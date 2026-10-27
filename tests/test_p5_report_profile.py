"""P5 T5.4 (#113): tools/report.py groups by profile and shows the model mix."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import report

ROWS = [
    {"ts": "2026-10-07T10:00:00", "audio_s": 3, "release_to_text_ms": 900},                                   # old row: no profile = lean
    {"ts": "2026-10-28T10:00:00", "profile": "lean", "audio_s": 20, "release_to_text_ms": 5000},
    {"ts": "2026-10-29T10:00:00", "profile": "cascade", "audio_s": 20, "release_to_text_ms": 1000, "models": {"prime": 2, "swift": 1}},
    {"ts": "2026-10-29T10:01:00", "profile": "cascade", "audio_s": 3, "release_to_text_ms": 700, "models": {"apex": 1}},
]


def test_rows_group_by_profile_and_old_rows_are_lean():
    g = report.by_profile(ROWS)
    assert {k: len(v) for k, v in g.items()} == {"lean": 2, "cascade": 2}


def test_model_mix_sums_chunks_per_model():
    assert report.model_mix(report.by_profile(ROWS)["cascade"]) == {"prime": 2, "swift": 1, "apex": 1}
    assert report.model_mix(report.by_profile(ROWS)["lean"]) == {}

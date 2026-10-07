"""S3.4 T12 (#85): tools/report.py summarises stats rows per length bucket."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import report

ROWS = [
    {"ts": "2026-10-07T10:00:00", "audio_s": 3, "release_to_text_ms": 900, "wait_ms": 0, "final_asr_ms": 500, "insert_ms": 10},
    {"ts": "2026-10-07T10:01:00", "audio_s": 4, "release_to_text_ms": 1100, "wait_ms": 0, "final_asr_ms": 700, "insert_ms": 10},
    {"ts": "2026-10-07T10:02:00", "audio_s": 20, "release_to_text_ms": 5000, "wait_ms": 0, "final_asr_ms": 4600, "insert_ms": 10},
    {"ts": "2026-10-08T10:00:00", "audio_s": 20, "release_to_text_ms": 1000, "wait_ms": 100, "final_asr_ms": 700, "insert_ms": 10},
    {"ts": "2026-10-08T10:01:00", "audio_s": 40, "release_to_text_ms": 1300, "wait_ms": 200, "final_asr_ms": 700, "insert_ms": 10},
    {"ts": "2026-10-08T10:02:00", "audio_s": 2, "release_to_text_ms": 800, "wait_ms": 0, "final_asr_ms": 400, "insert_ms": 10},
]


def test_buckets_and_percentiles():
    s = report.summarize(ROWS)
    assert s["<5s"]["n"] == 3 and s["<5s"]["p50"] == 900
    assert s["15-30s"]["n"] == 2 and s["15-30s"]["p90"] == 5000
    assert s["30s+"]["n"] == 1


def test_before_after_delta():
    before, after = report.split(ROWS, "2026-10-08")
    assert len(before) == 3 and len(after) == 3
    assert report.p50([r["release_to_text_ms"] for r in after]) < report.p50([r["release_to_text_ms"] for r in before])

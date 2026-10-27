"""P3 (#111): expected_left(e) = median talk time still to come, given e seconds already talked, from his own history."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "macos"))
import dictate as d

HIST = [3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 16, 18, 20, 25, 30, 35, 40, 45, 50, 60]   # 20 talk lengths in seconds


def test_at_zero_it_is_the_median_talk_length():
    assert d.expected_left(0, HIST) == 15.0            # (14 + 16) / 2


def test_only_longer_talks_count_and_e_is_subtracted():
    assert d.expected_left(10, HIST) == 17.5           # talks over 10 s, minus 10, median of 12 values


def test_talking_past_every_past_talk_falls_back():
    assert d.expected_left(100, HIST) == d.FALLBACK_LEFT_S


def test_no_history_falls_back():
    assert d.expected_left(5, []) == d.FALLBACK_LEFT_S


def test_loader_reads_audio_s_from_stats_jsonl(tmp_path):
    p = tmp_path / "stats.jsonl"
    p.write_text("\n".join(json.dumps({"audio_s": float(x)}) for x in range(1, 41)) + "\n")
    assert d.talk_history(p) == [float(x) for x in range(1, 41)]


def test_loader_with_under_30_rows_gives_no_history(tmp_path):
    p = tmp_path / "stats.jsonl"
    p.write_text("\n".join(json.dumps({"audio_s": float(x)}) for x in range(1, 21)) + "\n")
    assert d.talk_history(p) == []
    assert d.expected_left(5, d.talk_history(p)) == d.FALLBACK_LEFT_S


def test_loader_skips_rows_without_audio_s_and_a_missing_file(tmp_path):
    p = tmp_path / "stats.jsonl"
    p.write_text("\n".join(json.dumps({"audio_s": 5.0} if i % 2 else {"words": 3}) for i in range(80)) + "\n")
    assert len(d.talk_history(p)) == 40
    assert d.talk_history(tmp_path / "nope.jsonl") == []


def test_a_corrupt_stats_line_is_skipped_not_fatal(tmp_path):
    p = tmp_path / "stats.jsonl"
    rows = [json.dumps({"audio_s": float(x)}) for x in range(1, 41)]
    rows.insert(7, '{"audio_s": 5.0, "ts": "2026-10')          # a half-written line, e.g. a crash mid-append
    p.write_text("\n".join(rows) + "\n")
    assert len(d.talk_history(p)) == 40

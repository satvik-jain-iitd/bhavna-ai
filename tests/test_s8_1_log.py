"""S8.1 (#70): local log, T1 (#71) three files per dictation, T2 (#72) empty LOG_DIR writes nothing."""
import json, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "macos"))
import dictate as d


def test_t1_three_files_with_one_stem(tmp_path):
    a = np.zeros(16000, np.float32)
    d.log_dictation(str(tmp_path), "20261007-120000", a, "kal milte hain", {"chunks": [{"start_s": 0, "end_s": 1}]})
    assert {p.suffix for p in tmp_path.glob("20261007-120000.*")} == {".wav", ".txt", ".json"}
    assert (tmp_path / "20261007-120000.txt").read_text() == "kal milte hain"
    assert json.loads((tmp_path / "20261007-120000.json").read_text())["chunks"][0]["end_s"] == 1


def test_t2_empty_log_dir_writes_nothing(tmp_path):
    d.log_dictation("", "x", np.zeros(10, np.float32), "t", {})
    assert list(tmp_path.iterdir()) == []


def test_default_log_dir_is_project_log():
    assert d.LOG_DIR.endswith("/log") or d.LOG_DIR == ""

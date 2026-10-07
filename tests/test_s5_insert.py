"""S5.1 / S5.2: AX only when the focused element says the attribute is settable; stats records the insert method."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "macos"))
import dictate as d


def test_s5_2_ax_not_settable_falls_back_to_paste(monkeypatch):
    monkeypatch.setattr(d, "ax_insert", lambda text: False)          # terminals: AX says ok, inserts nothing -> we now return False
    calls = []
    monkeypatch.setattr(d, "paste_insert", lambda text, kb, shift=False: calls.append(text) or True)
    assert d.insert("hello", kb=None, how="ax_then_paste") == "paste"
    assert calls == ["hello"]


def test_s5_1_ax_settable_uses_ax(monkeypatch):
    monkeypatch.setattr(d, "ax_insert", lambda text: True)
    monkeypatch.setattr(d, "paste_insert", lambda *a, **k: (_ for _ in ()).throw(AssertionError("paste called")))
    assert d.insert("hello", kb=None, how="ax_then_paste") == "ax"


def test_s2_6_stats_row_records_insert_method(tmp_path):
    p = tmp_path / "stats.jsonl"
    d.stats(p, "a b", route="hinglish", lid_ms=0, asr_ms=800, insert_ms=5, audio_s=2.0, insert="paste")
    assert json.loads(p.read_text())["insert"] == "paste"

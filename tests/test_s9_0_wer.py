"""S9.0 T1: tools/wer.py gives WER and the gap list."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import wer


def test_wer_and_gaps():
    ref = "Kal subah wali meeting ko evening shift kar do aur Rahul ko email bhej dena."
    hyp = "Kal subah vaali meeting ko evening shift kar do aur raahul ko email bhej dena"
    r = wer.score(ref, hyp)
    assert r["n_ref"] == 14 and r["errors"] == 2 and abs(r["wer"] - 2 / 14) < 1e-9
    assert r["gaps"] == [("wali", "vaali"), ("rahul", "raahul")]


def test_perfect_and_deletion():
    assert wer.score("a b c", "a b c")["wer"] == 0
    r = wer.score("a b c d", "a c d"); assert r["errors"] == 1 and r["gaps"] == [("b", "")]

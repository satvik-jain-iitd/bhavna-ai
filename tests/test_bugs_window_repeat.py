"""Bugs #88 (tight window → 'nan') and #89 (repetition loop): window slack and the repeat guard."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "macos"))
import dictate as d


def test_window_leaves_one_second_of_silence():
    assert d.window_s(5.0) == 6 and d.window_s(4.2) == 6 and d.window_s(0.5) == 2
    assert d.window_s(29.5) == 30 and d.window_s(40.0) == 30


def test_repeat_guard_collapses_loops_and_counts():
    s = "Weekend par ham sab ja rahe hain. " + "To Friday ko jaldi niklana hai. " * 13
    out, n = d.collapse_repeats(s)
    assert out.strip() == "Weekend par ham sab ja rahe hain. To Friday ko jaldi niklana hai."
    assert n == 12


def test_repeat_guard_keeps_honest_text():
    s = "haan haan theek hai, kal kal milte hain"
    out, n = d.collapse_repeats(s)
    assert out == s and n == 0

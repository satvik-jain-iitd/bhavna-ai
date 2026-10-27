"""P3 T3.3 (#111): tools/report.py --left prints expected_left at e = 2, 5, 10, 20, 40 s."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import report

HIST = [3, 4, 5, 6, 7, 8, 9, 10, 12, 14, 16, 18, 20, 25, 30, 35, 40, 45, 50, 60]


def test_left_table_has_the_five_points_in_order():
    t = report.left_table(HIST)
    assert [e for e, _ in t] == [2, 5, 10, 20, 40]
    assert dict(t)[10] == 17.5


def test_left_table_with_no_history_shows_the_fallback():
    assert all(v == 3.0 for _, v in report.left_table([]))


def test_left_table_can_show_the_careful_slack_that_pick_uses():
    assert dict(report.left_table(HIST, q=0.1))[2] < dict(report.left_table(HIST))[2]

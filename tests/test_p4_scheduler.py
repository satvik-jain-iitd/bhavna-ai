"""P4 (#112): the cascade scheduler. Pure functions: which model gets a chunk, from slack, RAM and the talk-length history."""
import sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "macos"))
import dictate as d

RTF = {"swift": 0.1, "apex": 0.25, "prime": 0.5}
HIST = [20.0] * 40            # he always talks 20 s: after e seconds, 20 - e are left
FREE = 4000                   # MB free, above the floor


def pick(len_s, backlog_s, e, free_mb=FREE):
    return d.pick(len_s, backlog_s, e, HIST, free_mb, RTF)


# T4.3 the slack choice: Prime if backlog + len*RTF_prime <= expected_left(e), else Apex if it fits, else Swift
def test_plenty_of_slack_picks_prime():
    assert pick(8, 0, 0)[0] == "prime"            # 0 + 8*0.5 = 4 <= 20

def test_prime_too_slow_but_apex_fits_picks_apex():
    assert pick(8, 3, 14)[0] == "apex"            # left 6: prime 3+4=7 > 6, apex 3+2=5 <= 6

def test_nothing_fits_picks_swift():
    assert pick(8, 5, 14)[0] == "swift"           # left 6: apex 5+2=7 > 6

def test_prime_edge_is_inclusive():
    assert pick(8, 0, 16)[0] == "prime"           # left 4: prime exactly 4

def test_apex_edge_is_inclusive():
    assert pick(8, 2, 16)[0] == "apex"            # left 4: prime 6 > 4, apex 2+2 = 4

def test_the_reason_names_slack_and_choice():
    model, reason = pick(8, 0, 0)
    assert "slack" in reason and "prime" in reason


# T4.4 the last chunk, at release: Apex only if it fits the budget, else Swift
def test_last_chunk_short_enough_for_apex():
    assert d.pick_last(2.5, RTF) == "apex"        # 2.5*0.25 = 0.625 <= 0.7

def test_last_chunk_too_long_for_apex_goes_swift():
    assert d.pick_last(3.0, RTF) == "swift"       # 0.75 > 0.7


# T4.5 RAM floor: below it, Prime is never picked
def test_under_the_ram_floor_prime_is_never_picked():
    assert pick(8, 0, 0, free_mb=d.RAM_FLOOR_MB - 1)[0] == "apex"


# T4.6 catch-up: a Swift-done chunk goes to Prime again only if slack remains, never after release
def test_swift_chunk_is_redone_when_prime_still_fits():
    assert d.redo_with_prime(8, 0, 0, HIST, FREE, RTF, released=False) is True

def test_no_redo_after_release_or_without_slack():
    assert d.redo_with_prime(8, 0, 0, HIST, FREE, RTF, released=True) is False
    assert d.redo_with_prime(8, 9, 14, HIST, FREE, RTF, released=False) is False


# B8 the scheduler costs under 5 ms per chunk
def test_scheduler_is_fast():
    t = time.perf_counter()
    for _ in range(1000): d.pick(8, 1, 5, HIST, FREE, RTF)
    assert (time.perf_counter() - t) / 1000 < 0.005

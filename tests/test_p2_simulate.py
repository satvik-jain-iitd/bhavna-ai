"""P2 T2.7a (#110): tools/simulate.py replays logged chunk timing through a policy with no model run. One FIFO worker."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import simulate

RTF = {"swift": 0.1, "apex": 0.2, "prime": 0.5}


def cost(c, m): return (c["end_s"] - c["start_s"]) * RTF[m]      # seconds this model needs for this chunk
CH = [{"start_s": 0.0, "end_s": 8.0}, {"start_s": 8.0, "end_s": 9.0}]   # cut at 8 s, last chunk flushed at release (9 s)


def apex(len_s, queued_s, e, released): return "apex"


def test_release_to_text_is_the_wait_for_the_last_chunk_plus_postroll_and_insert():
    # chunk 1 decodes 8 -> 9.6, chunk 2 waits for it, decodes 9.6 -> 9.8; text at 9.8, release was 9.0 - 0.3 postroll
    assert abs(simulate.simulate(CH, 9.0, apex, cost) - (9.8 - 9.0 + 0.3 + 0.05)) < 1e-9


def test_a_fast_model_for_the_last_chunk_shortens_the_wait():
    def last_swift(len_s, queued_s, e, released): return "swift" if released else "apex"
    assert simulate.simulate(CH, 9.0, last_swift, cost) < simulate.simulate(CH, 9.0, apex, cost)


def test_when_the_worker_is_idle_at_release_only_postroll_and_insert_remain():
    ch = [{"start_s": 0.0, "end_s": 2.0}]
    assert abs(simulate.simulate(ch, 20.0, apex, cost) - (0.3 + 0.05)) < 1e-9


def test_cost_can_come_from_the_logged_decode_time():
    ch = [{"start_s": 0.0, "end_s": 8.0, "ms": 4000}]                  # the machine really took 4 s for this chunk
    assert abs(simulate.simulate(ch, 8.0, apex, lambda c, m: c["ms"] / 1000) - (4.0 + 0.3 + 0.05)) < 1e-9

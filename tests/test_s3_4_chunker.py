"""S3.4 (#58): Chunker T1 to T6 (#59 to #64), worker T7, T8 (#65, #66), route-once T9 (#67). Pure logic."""
import queue, sys, threading, time
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "macos"))
import dictate as d

SR, BLOCK = 16000, 1600
rng = np.random.default_rng(0)

def speech(sec):
    """Noise with a syllable-like envelope: loud and soft parts, never silent (real speech has gaps between words)."""
    t = np.arange(int(sec * SR)) / SR
    return (rng.standard_normal(len(t)) * 0.3 * (0.55 + 0.45 * np.sin(2 * np.pi * 3 * t))).astype(np.float32)
def silence(sec): return (rng.standard_normal(int(sec * SR)) * 0.002).astype(np.float32)

def feed(ch, a, preroll=True):
    """Real dictations always start with 0.5 s of pre-roll room noise; the tests do the same."""
    if preroll and not ch.blocks and not ch.band_log: a = np.concatenate([silence(0.5), a])
    out = []
    for i in range(0, len(a) - len(a) % BLOCK, BLOCK): out += ch.push(a[i:i + BLOCK])
    return out


def test_t1_short_dictation_is_one_chunk_at_release():
    ch = d.Chunker(); assert feed(ch, speech(3.0)) == []
    last = ch.flush(final=True); assert last is not None and 2.5 * SR <= len(last) <= 3.6 * SR
    assert ch.bounds[-1]["kind"] == "final"


def test_t2_continuous_speech_is_force_cut_before_max_and_nothing_lost():
    ch = d.Chunker(); a = speech(20.0); out = feed(ch, a); last = ch.flush(final=True)
    assert out and all(len(c) <= d.MAX_CHUNK_S * SR for c in out)
    assert ch.bounds[0]["kind"] == "forced"
    kept = sum(len(c) for c in out) + len(last)
    assert kept >= 0.95 * len(a)                       # only trim margins may go


def test_t3_cut_lands_inside_the_pause_after_min_chunk():
    ch = d.Chunker(); a = np.concatenate([speech(5.0), silence(0.4), speech(3.0)]); out = feed(ch, a)
    assert len(out) == 1
    end = ch.bounds[0]["end_s"]; assert 5.5 <= end <= 5.9 and ch.bounds[0]["kind"] == "pause"   # 0.5 s pre-roll shifts it


def test_t4_short_pauses_do_not_cut_before_min_chunk():
    ch = d.Chunker()
    assert feed(ch, np.concatenate([speech(1.0), silence(0.9), speech(1.0), silence(0.5)])) == []   # 3.9 s with pre-roll: under MIN_CHUNK_S
    assert len(feed(ch, np.concatenate([speech(1.0), silence(0.5)]))) == 1                             # past 4 s, next pause cuts


def test_t5_leading_silence_is_trimmed():
    ch = d.Chunker(); feed(ch, np.concatenate([silence(3.0), speech(2.0)])); last = ch.flush(final=True)
    assert last is not None and len(last) <= (2.0 + 1.0) * SR + BLOCK            # at most 1 s of leading room kept
    assert ch.bounds[-1]["start_s"] >= 3.5 - 1.0 - 0.1


def test_t6_silence_only_is_not_emitted():
    ch = d.Chunker(); assert feed(ch, silence(6.0)) == []
    assert ch.flush(final=True) is None


def test_t7_worker_keeps_order_and_reports_backlog():
    q, out = queue.Queue(), d.WorkerOut()
    def slow(a, prompt=None): time.sleep(0.05); return f"c{int(a[0])}"
    threading.Thread(target=d.run_worker, args=(q, slow, out), daemon=True).start()
    for i in range(5): q.put(np.full(10, i, np.float32))
    t_q = time.perf_counter(); q.put(None); out.done.wait(5)
    assert [r["text"] for r in out.items] == ["c0", "c1", "c2", "c3", "c4"]
    assert out.items[-1]["t_start"] - t_q > 0.1        # the last chunk waited behind earlier ones


def test_t8_one_failing_chunk_does_not_lose_the_others():
    q, out = queue.Queue(), d.WorkerOut()
    def flaky(a, prompt=None):
        if int(a[0]) == 2: raise RuntimeError("boom")
        return f"c{int(a[0])}"
    threading.Thread(target=d.run_worker, args=(q, flaky, out), daemon=True).start()
    for i in range(4): q.put(np.full(10, i, np.float32))
    q.put(None); out.done.wait(5)
    assert [r["text"] for r in out.items] == ["c0", "c1", "", "c3"] and out.errors == 1


def test_t9_full_profile_runs_lid_once_per_dictation():
    calls = []
    class M: lid = staticmethod(lambda a: calls.append(1) or {"en": 0.95}); en = None; hinglish = None
    r = d.RouteOnce(M(), "auto", "full")
    assert [r(np.zeros(10)) for _ in range(3)] == ["en", "en", "en"] and len(calls) == 1
    assert d.RouteOnce(M(), "auto", "lean")(np.zeros(10)) == "hinglish" and len(calls) == 1

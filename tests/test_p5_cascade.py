"""P5 (#113): the cascade profile. Fake models only: no real model is loaded in these tests."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "macos"))
import dictate as d

HIST = [20.0] * 40            # he always talks 20 s: after e seconds, 20 - e are left
SR = d.SR
RTF = {"swift": 0.1, "apex": 0.25, "prime": 0.5}


class Clock:
    def __init__(self): self.t = 0.0
    def __call__(self): return self.t


def audio(seconds): return [0.0] * int(seconds * SR)


def make(free_mb=4000):
    loads = []
    fake = {m: (lambda a, prompt=None, m=m: m) for m in ("swift", "apex", "prime")}
    def loader(): loads.append("prime"); return fake["prime"]
    c = d.Cascade({"swift": fake["swift"], "apex": fake["apex"]}, loader, history=HIST, rtf=RTF, free_mb=lambda: free_mb, clock=Clock())
    return c, loads


# T5.1 lazy holder
def test_prime_is_not_loaded_until_asked():
    _, loads = make(); assert loads == []

def test_prime_loads_once_then_unloads_after_idle():
    clock, loads = Clock(), []
    h = d.LazyModel(lambda: loads.append(1) or "m", idle_s=300, clock=clock)
    assert h.get() == "m" and h.get() == "m" and len(loads) == 1
    clock.t = 301; h.unload_if_idle(); assert h.model is None
    h.get(); assert len(loads) == 2

def test_prime_is_kept_while_not_idle():
    clock = Clock(); h = d.LazyModel(lambda: "m", idle_s=300, clock=clock)
    h.get(); clock.t = 299; h.unload_if_idle(); assert h.model == "m"


# T5.2 the worker function picks by slack
def test_a_chunk_in_a_long_talk_goes_to_prime_and_loads_it():
    c, loads = make()
    assert c(audio(8), None, e=15) == "prime" and loads == ["prime"]      # left 5, prime 4 fits, talk over PRIME_MIN_TALK_S

def test_a_short_talk_does_not_load_prime():
    c, loads = make()
    assert c(audio(8), None, e=0) == "apex" and loads == []               # slack says prime, but it is not worth a load yet

def test_a_backlog_pushes_the_chunk_to_swift():
    c, _ = make()
    assert c(audio(8), None, e=15, queued_s=40) == "swift"                # backlog 40 x 0.25 = 10 s > 5 s left

def test_low_ram_never_picks_prime():
    c, loads = make(free_mb=500)
    assert c(audio(8), None, e=15) == "apex" and loads == []

def test_after_release_the_last_budget_decides():
    c, _ = make()
    assert c(audio(2), None, e=30, released=True) == "apex"               # 2 x 0.25 = 0.5 <= 0.7
    assert c(audio(4), None, e=30, released=True) == "swift"              # 1.0 > 0.7

def test_the_prompt_reaches_the_model():
    seen = []
    c = d.Cascade({"swift": lambda a, prompt=None: seen.append(prompt) or "s", "apex": lambda a, prompt=None: seen.append(prompt) or "a"},
                  lambda: None, history=HIST, rtf=RTF, free_mb=lambda: 4000, clock=Clock())
    c(audio(2), "pichhla vaakya", e=0); assert seen == ["pichhla vaakya"]


# T5.3 the decision log
def test_every_chunk_logs_model_and_reason_in_order():
    c, _ = make()
    c(audio(8), None, e=0); c(audio(8), None, e=15)
    assert [x["model"] for x in c.log] == ["apex", "prime"]
    assert all("slack" in x["reason"] or "release" in x["reason"] for x in c.log)
    assert c.counts() == {"apex": 1, "prime": 1}


# RAM reading
VM = "Mach Virtual Memory Statistics: (page size of 16384 bytes)\nPages free:                      6353.\nPages active:                   94792.\nPages inactive:                 87669.\nPages speculative:               1000.\n"

def test_free_ram_is_free_plus_inactive_plus_speculative():
    assert d.free_ram_mb(VM) == (6353 + 87669 + 1000) * 16384 // 2**20


# review of #117 (bhavna-dev): bug #89 retry, double load, vm_stat per chunk
def test_the_bug_89_retry_logs_one_row_per_chunk():
    import queue
    calls = []
    def looping(a, prompt=None): calls.append(prompt); return "kya haal hai " * 5 if len(calls) == 1 else "kya haal hai"      # a looping phrase: run_worker retries once
    c = d.Cascade({"swift": looping, "apex": looping}, lambda: None, history=HIST, rtf=RTF, free_mb=lambda: 4000, clock=Clock())
    q, out, a = queue.Queue(), d.WorkerOut(), audio(2)
    q.put(a); q.put(None)
    d.run_worker(q, lambda x, prompt=None: c(x, prompt, e=0), out)
    assert len(calls) == 2 and len(out.items) == 1 and len(c.log) == 1 and c.counts() == {"apex": 1}


def test_two_threads_asking_for_prime_load_it_once():
    import threading, time as t
    loads = []
    h = d.LazyModel(lambda: (loads.append(1), t.sleep(0.05), "m")[2], idle_s=300, clock=Clock())
    ts = [threading.Thread(target=h.get) for _ in range(2)]
    [x.start() for x in ts]; [x.join() for x in ts]
    assert len(loads) == 1


def test_unloading_prime_calls_the_release_hook():
    clock, released = Clock(), []
    h = d.LazyModel(lambda: "m", idle_s=300, clock=clock, on_unload=lambda: released.append(1))
    h.get(); clock.t = 301; h.unload_if_idle()
    assert released == [1]


def test_free_ram_is_read_at_most_once_per_few_seconds():
    n, clock = [], Clock()
    c = d.Cascade({"swift": lambda a, prompt=None: "s", "apex": lambda a, prompt=None: "a"}, lambda: None, history=HIST, rtf=RTF,
                  free_mb=lambda: n.append(1) or 4000, clock=clock)
    c(audio(2), None, e=0); c(audio(2), None, e=1)
    assert len(n) == 1
    clock.t = 10; c(audio(2), None, e=2)
    assert len(n) == 2

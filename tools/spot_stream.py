#!/usr/bin/env python3
"""T10 (#68): feed a long synthetic Hinglish clip in REAL TIME through Chunker + worker + Models(lean),
then measure the release-to-text identity exactly as dictate.py does. One model loaded."""
import queue, sys, threading, time, wave
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "macos")); import dictate as d

a = np.frombuffer(wave.open(sys.argv[1]).readframes(10**9), np.int16).astype(np.float32) / 32768
m = d.Models("lean"); q, out, ch = queue.Queue(), d.WorkerOut(), d.Chunker()
threading.Thread(target=d.run_worker, args=(q, m.hinglish, out), daemon=True).start()
t0 = time.perf_counter()
for i in range(0, len(a) - len(a) % d.BLOCK, d.BLOCK):              # real-time feed: one 100 ms block per 100 ms
    for c in ch.push(a[i:i + d.BLOCK]): q.put(c)
    time.sleep(max(0, t0 + (i + d.BLOCK) / d.SR - time.perf_counter()))
t_up = time.perf_counter(); time.sleep(d.POSTROLL_S)
last = ch.flush(final=True); t_fq = time.perf_counter()
if last is not None: q.put(last)
q.put(None); out.done.wait(); t_done = time.perf_counter()
text = " ".join(r["text"] for r in out.items if r["text"]); fin = out.items[-1]
wait = max(0, (fin["t_start"] - t_fq) * 1000); rel = (t_done - t_up) * 1000
kinds = [b["kind"] for b in ch.bounds]
print(f"audio {len(a)/d.SR:.1f}s  chunks {len(out.items)} (pause {kinds.count('pause')} forced {kinds.count('forced')})  "
      f"release→text {rel:.0f}ms = postroll {d.POSTROLL_S*1000:.0f} + wait {wait:.0f} + final {fin['ms']} (+insert)  "
      f"asr_total {sum(r['ms'] for r in out.items)}ms rtf {sum(r['ms'] for r in out.items)/(len(a)/d.SR*1000):.2f}  errors {out.errors} repeats {out.repeats}")
for b, r in zip(ch.bounds, out.items): print(f"  {b['start_s']:5.1f}-{b['end_s']:5.1f}s {b['kind']:6} {r['ms']:5d}ms  {r['text']}")
print("TEXT:", text); print("words", len(text.split()))

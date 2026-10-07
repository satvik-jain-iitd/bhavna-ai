#!/usr/bin/env python3
"""Bhavna.ai, macOS. Hold the key, speak Hindi / English / both, release. Your exact words land at the cursor.
Run: uv run --project macos macos/dictate.py
"""
import json, math, os, platform, queue, subprocess, sys, threading, time, wave
from collections import deque
from pathlib import Path
import numpy as np

PROFILE = "lean"           # lean = Apex only (~0.9 GB, English too) | full = tiny + Parakeet + Apex (~2.3 GB)  (ADR-012)
MODELS_FOR = {"lean": ("apex-mlx-q8",), "full": ("tiny-mlx", "parakeet-v2-mlx", "apex-mlx-q8")}
WINDOW_SLACK_S, WINDOW_MAX_S = 1.0, 30   # Apex encoder window: clip + 1 s of silence, whole seconds, max 30 (ADR-012, bugs #88 #89)
MODE = "auto"              # auto | en | hinglish   (what a key does by default; lean ignores it, everything is Apex)
KEYS = {"alt_r": MODE}     # pynput key name -> mode. Two-key layout: {"alt_r": "en", "cmd_r": "hinglish"}
INSERT = "ax_then_paste"   # ax | paste | paste_shift | type | ax_then_paste   (owner's feel test, S5.0)
EN_THRESHOLD = 0.8         # tiny LID p(en) at or above this -> Parakeet, else Apex (ADR-002)
SR, BLOCK, PREROLL_S, POSTROLL_S, MIN_S = 16000, 1600, 0.5, 0.3, 0.3
# S3.4 transcribe while talking (ADR-013): cut chunks at pauses, transcribe in the background, insert once at release
PAUSE_S, MIN_CHUNK_S, MAX_CHUNK_S = 0.25, 4.0, 12.0     # cut after ≥ MIN_CHUNK_S when a pause ≥ PAUSE_S shows; force-cut at MAX_CHUNK_S
SPEECH_MIN_S, MIN_SPEECH_RUN_S, MARGIN_S = 1.0, 0.25, 0.2  # a chunk needs ≥ SPEECH_MIN_S of speech; a burst < MIN_SPEECH_RUN_S is a click; trim margins
CONTEXT_WORDS = 20         # previous chunk's last words go to the decoder as prompt (0 = off)
ROOT = Path(__file__).resolve().parents[1]
MODELS, STATS = ROOT / "models", ROOT / "stats.jsonl"
LOG_DIR = os.environ.get("LOG_DIR", str(ROOT / "log"))  # S8.1: on by default, local only; LOG_DIR="" turns it off
SOUNDS = ("/System/Library/Sounds/Tink.aiff", "/System/Library/Sounds/Pop.aiff")  # start, done
SOUND_VOLUME = 3.0         # afplay -v multiplier; 1 = system file level


class Ring:
    """Mic stream is always open. Keeps PREROLL_S of audio while idle; collects everything while recording."""
    def __init__(self, preroll_s=PREROLL_S, sr=SR):
        self.pre, self.pre_n, self.rec = deque(), int(preroll_s * sr), None

    def push(self, block):
        if self.rec is not None:
            self.rec.append(block); return
        self.pre.append(block)
        while sum(len(b) for b in self.pre) - len(self.pre[0]) >= self.pre_n:
            self.pre.popleft()

    def start(self): self.rec = list(self.pre)

    def stop(self):
        a = np.concatenate(self.rec) if self.rec else np.zeros(0, np.float32)
        self.rec = None; return a


def too_short(a): return len(a) < MIN_S * SR


def stats(path, text, **row):
    row = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), **row, "words": len(text.split())}
    with open(path, "a") as f: f.write(json.dumps(row) + "\n")


def translated():
    return subprocess.run(["sysctl", "-n", "sysctl.proc_translated"], capture_output=True, text=True).stdout.strip() == "1"


def native(): return platform.machine() == "arm64" and not translated()  # ADR-008


def beep(i): subprocess.Popen(["afplay", "-v", str(SOUND_VOLUME), SOUNDS[i]])


def window_s(seconds):
    """Whole seconds, always ≥ 1 s of silence after the speech (whisper loops or emits 'nan' without it), max 30."""
    return int(min(WINDOW_MAX_S, max(2, math.ceil(seconds + WINDOW_SLACK_S))))


def collapse_repeats(text, min_words=3, keep=1):
    """Whisper loop guard (bug #89): a phrase of ≥ min_words that repeats back to back is kept once. Returns (text, removed)."""
    words = text.split(); n = len(words); i = 0; out = []; removed = 0
    while i < n:
        hit = False
        for L in range(min_words, min(12, (n - i) // 2) + 1):      # shortest period first
            seg = words[i:i + L]; k = 1
            while words[i + k * L:i + (k + 1) * L] == seg: k += 1
            if k > 2:
                out += seg; removed += k - 1; i += k * L; hit = True; break
        if not hit: out.append(words[i]); i += 1
    return " ".join(out), removed


def quietest(a, lo, hi, frame=320):
    """Sample index of the quietest 20 ms frame in a[lo:hi]."""
    n = (hi - lo) // frame * frame
    frames = a[lo:lo + n].reshape(-1, frame)
    return lo + int(np.argmin(np.abs(frames).mean(axis=1))) * frame


def pieces(a, max_s=WINDOW_MAX_S, search_s=2.0):
    """Split audio longer than max_s into pieces of at most max_s, cutting at the quietest 20 ms frame
    in the last search_s before each boundary (bug #56: whisper's 30 s context would drop the tail)."""
    out, start = [], 0
    while len(a) - start > max_s * SR:
        cut = quietest(a, start + int((max_s - search_s) * SR), start + int(max_s * SR))
        out.append(a[start:cut]); start = cut
    out.append(a[start:]); return out


class Chunker:
    """Fed the mic blocks while recording. Emits a chunk at a pause after MIN_CHUNK_S, or force-cuts at MAX_CHUNK_S.
    Chunks are trimmed to speech bounds (+ MARGIN_S). Pure logic: no threads, no model."""
    def __init__(self, sr=SR, block=BLOCK):
        self.sr, self.block, self.blocks, self.loud, self.floor = sr, block, [], [], None
        self.offset, self.bounds, self.quiet_run, self.speech_run = 0, [], 0, 0

    def _is_speech(self, b):
        rms = float(np.sqrt(np.mean(b * b)))
        if self.floor is None: self.floor = min(rms, 0.02)            # first block is pre-roll room noise
        speech = rms > max(3 * self.floor, 0.005) or rms > 0.02       # 0.02 is clear speech in any room
        if not speech: self.floor = 0.9 * self.floor + 0.1 * rms      # the floor follows quiet blocks only
        return speech

    def push(self, b):
        sp = self._is_speech(b); self.blocks.append(b); self.loud.append(sp)
        if sp:
            self.speech_run += 1
            if self.speech_run * self.block >= MIN_SPEECH_RUN_S * self.sr: self.quiet_run = 0
        else:
            self.quiet_run += 1; self.speech_run = 0
        dur = len(self.blocks) * self.block / self.sr
        if dur >= MIN_CHUNK_S and self.quiet_run * self.block >= PAUSE_S * self.sr:
            return self._emit(len(self.blocks) - self.quiet_run + 1, "pause")   # keep ~100 ms of the pause
        if dur >= MAX_CHUNK_S:
            a = np.concatenate(self.blocks); cut = quietest(a, len(a) - self.sr, len(a))
            return self._emit(max(1, cut // self.block), "forced")
        return []

    def _emit(self, n_blocks, kind, final=False):
        blocks, loud = self.blocks[:n_blocks], self.loud[:n_blocks]
        if not any(loud): 
            if final: self.blocks, self.loud = [], []; return []
            return []  # silence so far: keep accumulating, nothing to say yet
        first, last = loud.index(True), len(loud) - 1 - loud[::-1].index(True)
        speech_s = sum(loud) * self.block / self.sr
        if not final and speech_s < SPEECH_MIN_S: return []           # too little speech: merge with what follows
        m = int(MARGIN_S * self.sr / self.block)
        lo, hi = max(0, first - m), min(n_blocks, last + 1 + m)
        chunk = np.concatenate(blocks[lo:hi])
        self.bounds.append({"start_s": round((self.offset + lo * self.block) / self.sr, 2),
                            "end_s": round((self.offset + hi * self.block) / self.sr, 2), "speech_s": round(speech_s, 2), "kind": kind})
        self.offset += n_blocks * self.block
        self.blocks, self.loud = self.blocks[n_blocks:], self.loud[n_blocks:]
        self.quiet_run = sum(1 for _ in range(len(self.loud)) if not self.loud[-1]) if self.loud else 0
        return [chunk]

    def flush(self, final=True):
        if not self.blocks: return None
        out = self._emit(len(self.blocks), "final", final=True)
        if out and sum(self.bounds[-1]["speech_s"] for _ in [0]) >= MIN_S: return out[0]
        if out: self.bounds.pop()
        return None

    def reset(self):
        self.__init__(self.sr, self.block)


class WorkerOut:
    def __init__(self): self.items, self.errors, self.repeats, self.done = [], 0, 0, threading.Event()


def run_worker(q, fn, out):
    """Transcribe chunks in order from q until None. fn(audio, prompt) -> text. Errors count, never stop."""
    prev = ""
    while True:
        a = q.get()
        if a is None: out.done.set(); return
        t0 = time.perf_counter()
        try:
            text, rep = collapse_repeats(fn(a, prompt=prev or None))
            if rep: text, rep2 = collapse_repeats(fn(a, prompt=None)); rep += rep2   # bug #89: retry once without the prompt
            out.repeats += rep
        except Exception as e: out.errors += 1; text = ""; print(f"chunk error: {e}")
        t1 = time.perf_counter()
        out.items.append({"text": text, "t_start": t0, "t_end": t1, "ms": round((t1 - t0) * 1000)})
        if text and CONTEXT_WORDS: prev = " ".join(text.split()[-CONTEXT_WORDS:])


class RouteOnce:
    """Full profile: language ID on the first chunk only; the route holds for the dictation (lean: always Apex)."""
    def __init__(self, m, mode, profile): self.m, self.mode, self.profile, self.r = m, mode, profile, None
    def __call__(self, a):
        if self.r is None:
            probs = self.m.lid(a) if self.profile == "full" and self.mode == "auto" and self.m.lid else {}
            self.r = route(probs, self.mode, self.profile)
        return self.r


def log_dictation(log_dir, stem, a, text, meta):
    """S8.1: wav + txt + json per dictation, local only. Empty log_dir = off."""
    if not log_dir: return
    Path(log_dir).mkdir(parents=True, exist_ok=True); stem = str(Path(log_dir) / stem)
    with wave.open(stem + ".wav", "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((a * 32767).astype(np.int16).tobytes())
    Path(stem + ".txt").write_text(text)
    Path(stem + ".json").write_text(json.dumps(meta, ensure_ascii=False, indent=1))


def route(probs, mode, profile=None):
    if (profile or PROFILE) == "lean": return "hinglish"
    if mode != "auto": return mode
    return "en" if probs.get("en", 0.0) >= EN_THRESHOLD else "hinglish"


class Models:
    """Apex (Hinglish and English). Full profile adds tiny (language ID) and Parakeet v2 (English). All resident (ADR-002, ADR-012)."""
    def __init__(self, profile=PROFILE):
        import mlx.core as mx, mlx.nn as nn
        from mlx_whisper.load_models import load_model
        from mlx_whisper.audio import log_mel_spectrogram, pad_or_trim, N_FRAMES, N_SAMPLES
        from mlx_whisper.decoding import decode, detect_language, DecodingOptions
        from mlx_whisper import whisper as W
        for p in MODELS_FOR[profile]:
            if not (MODELS / p).exists(): sys.exit(f"missing model folder: {MODELS / p}")

        def encoder_call(self, x):  # ADR-012: slice the sinusoid table to the window, like whisper.cpp audio_ctx
            x = nn.gelu(self.conv1(x)); x = nn.gelu(self.conv2(x))
            x = x + self._positional_embedding[: x.shape[1]]
            for block in self.blocks: x, _, _ = block(x)
            return self.ln_post(x)
        W.AudioEncoder.__call__ = encoder_call

        apex = load_model(str(MODELS / "apex-mlx-q8"), dtype=mx.float16)
        opts = DecodingOptions(language="en", task="transcribe", without_timestamps=True, temperature=0.0, fp16=True)

        def one(a, o=opts):
            w = window_s(len(a) / SR)
            mel = pad_or_trim(log_mel_spectrogram(a, n_mels=apex.dims.n_mels, padding=max(0, w * SR - len(a))), w * 100, axis=-2).astype(mx.float16)
            return decode(apex, mel, o).text.strip()

        def hinglish(a, prompt=None):
            o = DecodingOptions(language="en", task="transcribe", without_timestamps=True, temperature=0.0, fp16=True, prompt=prompt) if prompt else opts
            return " ".join(t for t in (one(p, o) for p in pieces(a)) if t)
        self.hinglish, self.lid, self.en = hinglish, None, None
        warm = np.zeros(SR, np.float32); hinglish(warm)
        if profile != "full": return

        from parakeet_mlx import from_pretrained
        from parakeet_mlx.audio import get_logmel
        tiny, pk = load_model(str(MODELS / "tiny-mlx"), dtype=mx.float16), from_pretrained(str(MODELS / "parakeet-v2-mlx"))

        def lid(a):
            mel = pad_or_trim(log_mel_spectrogram(a, n_mels=tiny.dims.n_mels, padding=N_SAMPLES), N_FRAMES, axis=-2).astype(mx.float16)
            probs = detect_language(tiny, mel)[1]
            return probs[0] if isinstance(probs, list) else probs

        def en(a, prompt=None): return pk.generate(get_logmel(mx.array(a), pk.preprocessor_config))[0].text.strip()
        self.lid, self.en = lid, en
        lid(warm); en(warm)


def ax_insert(text):
    from ApplicationServices import (AXUIElementCreateSystemWide, AXUIElementCopyAttributeValue, AXUIElementIsAttributeSettable,
                                     AXUIElementSetAttributeValue, kAXFocusedUIElementAttribute, kAXSelectedTextAttribute)
    err, el = AXUIElementCopyAttributeValue(AXUIElementCreateSystemWide(), kAXFocusedUIElementAttribute, None)
    if err != 0 or el is None: return False
    err, settable = AXUIElementIsAttributeSettable(el, kAXSelectedTextAttribute, None)  # terminals say "ok" then insert nothing (R4)
    if err != 0 or not settable: return False
    return AXUIElementSetAttributeValue(el, kAXSelectedTextAttribute, text) == 0


def paste_insert(text, kb, shift=False):
    from AppKit import NSPasteboard, NSPasteboardTypeString
    from pynput.keyboard import Key
    pb = NSPasteboard.generalPasteboard()
    old = pb.stringForType_(NSPasteboardTypeString)
    pb.clearContents(); pb.setString_forType_(text, NSPasteboardTypeString)
    pb.setString_forType_("1", "org.nspasteboard.ConcealedType")  # clipboard managers skip it
    mine = pb.changeCount()
    mods = (Key.cmd, Key.shift) if shift else (Key.cmd,)
    for m in mods: kb.press(m)
    kb.press("v"); kb.release("v")
    for m in reversed(mods): kb.release(m)

    def restore():
        if old is not None and pb.changeCount() == mine:
            pb.clearContents(); pb.setString_forType_(old, NSPasteboardTypeString)
    threading.Timer(0.3, restore).start()
    return True


def insert(text, kb, how=None):
    how = how or INSERT
    if how == "ax": return "ax" if ax_insert(text) else "ax-failed"
    if how == "ax_then_paste": return "ax" if ax_insert(text) else ("paste" if paste_insert(text, kb) else "paste-failed")
    if how == "paste": return "paste" if paste_insert(text, kb) else "paste-failed"
    if how == "paste_shift": return "paste_shift" if paste_insert(text, kb, shift=True) else "paste-failed"
    if how == "type": kb.type(text); return "type"
    raise ValueError(how)


def main():
    if not native(): sys.exit("arm64 only: run on Apple silicon without Rosetta")
    import sounddevice as sd
    from pynput import keyboard
    t0 = time.perf_counter(); m = Models(PROFILE); print(f"models ({PROFILE}): {' '.join(MODELS_FOR[PROFILE])} ✓ ({time.perf_counter() - t0:.1f} s)")
    kb, ring, busy = keyboard.Controller(), Ring(), threading.Lock()
    keys = {getattr(keyboard.Key, k): v for k, v in KEYS.items()}
    st = {"q": None, "out": None, "chunker": Chunker(), "route": None, "t_down": 0.0}

    def start(mode):
        st["q"], st["out"], st["chunker"] = queue.Queue(), WorkerOut(), Chunker()
        st["route"], st["t_down"] = RouteOnce(m, mode, PROFILE), time.perf_counter()
        def fn(a, prompt=None): return (m.en if st["route"](a) == "en" else m.hinglish)(a, prompt=prompt)
        threading.Thread(target=run_worker, args=(st["q"], fn, st["out"]), daemon=True).start()
        ring.start(); beep(0)

    def on_block(b):
        ring.push(b)
        if ring.rec is not None and st["q"] is not None:
            for c in st["chunker"].push(b): st["q"].put(c)

    def finish(t_up):
        time.sleep(POSTROLL_S)  # keep the last syllable spoken as the key comes up
        a = ring.stop(); q, out, ch = st["q"], st["out"], st["chunker"]; st["q"] = None
        last = ch.flush(final=True); t_final_q = time.perf_counter()
        if last is not None: q.put(last)
        q.put(None); out.done.wait()
        if too_short(a) or not out.items: print(f"dropped ({len(a) / SR:.1f}s)"); return
        text = " ".join(r["text"] for r in out.items if r["text"]); r = st["route"].r or "hinglish"
        t0 = time.perf_counter(); how = insert(text, kb) if text else "empty"; t1 = time.perf_counter()
        beep(1)
        fin = out.items[-1]; wait_ms = max(0.0, (fin["t_start"] - t_final_q) * 1000) if last is not None else 0.0
        rel = (t1 - t_up) * 1000; asr_total = sum(x["ms"] for x in out.items); audio_s = len(a) / SR
        kinds = [bd["kind"] for bd in ch.bounds]
        print(f"[{time.strftime('%H:%M:%S')}] {r:8} {len(out.items)} chunks  release→text {rel:4.0f}ms (wait {wait_ms:.0f} final {fin['ms']} insert {(t1 - t0) * 1000:.0f}) {how}  \"{text}\"")
        row = dict(route=r, release_to_text_ms=round(rel), postroll_ms=round(POSTROLL_S * 1000), wait_ms=round(wait_ms), final_asr_ms=fin["ms"],
                   insert=how, insert_ms=round((t1 - t0) * 1000), asr_total_ms=asr_total, rtf=round(asr_total / (audio_s * 1000), 3),
                   chunks=len(out.items), pause_cuts=kinds.count("pause"), forced_cuts=kinds.count("forced"),
                   audio_s=round(audio_s, 2), speech_s=round(sum(bd["speech_s"] for bd in ch.bounds), 2), errors=out.errors, repeats=out.repeats)
        stats(STATS, text, **row)
        stem = time.strftime("%Y%m%d-%H%M%S")
        meta = {**row, "profile": PROFILE, "constants": dict(PAUSE_S=PAUSE_S, MIN_CHUNK_S=MIN_CHUNK_S, MAX_CHUNK_S=MAX_CHUNK_S, CONTEXT_WORDS=CONTEXT_WORDS, WINDOW_SLACK_S=WINDOW_SLACK_S),
                "t_down_to_up_s": round(t_up - st["t_down"], 2), "chunks_detail": [{**bd, **{k: it[k] for k in ("text", "ms")}} for bd, it in zip(ch.bounds, out.items)], "text": text}
        log_dictation(LOG_DIR, stem, a, text, meta)

    def on_press(k):
        if k in keys and ring.rec is None and not busy.locked(): start(keys[k])

    def on_release(k):
        if k in keys and ring.rec is not None and busy.acquire(blocking=False):
            t_up = time.perf_counter()
            def run():
                try: finish(t_up)
                except Exception as e: print(f"error: {e}")
                finally: busy.release()
            threading.Thread(target=run, daemon=True).start()

    with sd.InputStream(samplerate=SR, channels=1, dtype="float32", blocksize=BLOCK,
                        callback=lambda d, *_: on_block(d[:, 0].copy())):
        print(f"hold {' / '.join(KEYS)} to talk (profile {PROFILE}, mode {MODE}, insert {INSERT}). ctrl-c to quit.")
        with keyboard.Listener(on_press=on_press, on_release=on_release) as L: L.join()


if __name__ == "__main__":
    main()

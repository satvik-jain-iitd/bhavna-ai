#!/usr/bin/env python3
"""Bhavna.ai, macOS. Hold the key, speak Hindi / English / both, release. Your exact words land at the cursor.
Run: uv run --project macos macos/dictate.py
"""
import json, math, os, platform, subprocess, sys, threading, time
from collections import deque
from pathlib import Path
import numpy as np

PROFILE = "lean"           # lean = Apex only (~0.9 GB, English too) | full = tiny + Parakeet + Apex (~2.3 GB)  (ADR-012)
MODELS_FOR = {"lean": ("apex-mlx-q8",), "full": ("tiny-mlx", "parakeet-v2-mlx", "apex-mlx-q8")}
WINDOW_STEP_S, WINDOW_MAX_S = 5, 30   # Apex encoder window: clip rounded up to the next step (ADR-012)
MODE = "auto"              # auto | en | hinglish   (what a key does by default; lean ignores it, everything is Apex)
KEYS = {"alt_r": MODE}     # pynput key name -> mode. Two-key layout: {"alt_r": "en", "cmd_r": "hinglish"}
INSERT = "ax_then_paste"   # ax | paste | paste_shift | type | ax_then_paste   (owner's feel test, S5.0)
EN_THRESHOLD = 0.8         # tiny LID p(en) at or above this -> Parakeet, else Apex (ADR-002)
SR, BLOCK, PREROLL_S, POSTROLL_S, MIN_S = 16000, 1600, 0.5, 0.3, 0.3
ROOT = Path(__file__).resolve().parents[1]
MODELS, STATS, LOG_DIR = ROOT / "models", ROOT / "stats.jsonl", os.environ.get("LOG_DIR")
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
    return min(WINDOW_MAX_S, max(WINDOW_STEP_S, math.ceil(seconds / WINDOW_STEP_S) * WINDOW_STEP_S))


def pieces(a, max_s=WINDOW_MAX_S, search_s=2.0, frame=320):
    """Split audio longer than max_s into pieces of at most max_s, cutting at the quietest 20 ms frame
    in the last search_s before each boundary (bug #56: whisper's 30 s context would drop the tail)."""
    out, start = [], 0
    while len(a) - start > max_s * SR:
        lo, hi = start + int((max_s - search_s) * SR), start + max_s * SR
        frames = a[lo:hi].reshape(-1, frame) if (hi - lo) % frame == 0 else a[lo:hi][: (hi - lo) // frame * frame].reshape(-1, frame)
        cut = lo + int(np.argmin(np.abs(frames).mean(axis=1))) * frame
        out.append(a[start:cut]); start = cut
    out.append(a[start:]); return out


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

        def one(a):
            w = window_s(len(a) / SR)
            mel = pad_or_trim(log_mel_spectrogram(a, n_mels=apex.dims.n_mels, padding=max(0, w * SR - len(a))), w * 100, axis=-2).astype(mx.float16)
            return decode(apex, mel, opts).text.strip()

        def hinglish(a): return " ".join(t for t in (one(p) for p in pieces(a)) if t)
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

        def en(a): return pk.generate(get_logmel(mx.array(a), pk.preprocessor_config))[0].text.strip()
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

    def finish(mode):
        time.sleep(POSTROLL_S)  # keep the last syllable spoken as the key comes up
        a = ring.stop()
        if too_short(a): print(f"dropped ({len(a) / SR:.1f}s)"); return
        t = time.perf_counter(); probs = m.lid(a) if m.lid and mode == "auto" else {}; r = route(probs, mode); lid_ms = (time.perf_counter() - t) * 1000
        t = time.perf_counter(); text = m.en(a) if r == "en" else m.hinglish(a); asr_ms = (time.perf_counter() - t) * 1000
        t = time.perf_counter(); how = insert(text, kb) if text else "empty"; ins_ms = (time.perf_counter() - t) * 1000
        beep(1)
        print(f"[{time.strftime('%H:%M:%S')}] {r:8} lid {lid_ms:4.0f}ms  asr {asr_ms:5.0f}ms  insert {how} {ins_ms:3.0f}ms   \"{text}\"")
        stats(STATS, text, route=r, lid_ms=round(lid_ms), asr_ms=round(asr_ms), insert=how, insert_ms=round(ins_ms), audio_s=round(len(a) / SR, 2))
        if LOG_DIR:
            import wave; stem = Path(LOG_DIR) / time.strftime("%Y%m%d-%H%M%S"); Path(LOG_DIR).mkdir(exist_ok=True)
            with wave.open(str(stem) + ".wav", "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((a * 32767).astype(np.int16).tobytes())
            Path(str(stem) + ".txt").write_text(text)

    def on_press(k):
        if k in keys and ring.rec is None and not busy.locked(): ring.start(); beep(0)

    def on_release(k):
        if k in keys and ring.rec is not None and busy.acquire(blocking=False):
            def run():
                try: finish(keys[k])
                except Exception as e: print(f"error: {e}")
                finally: busy.release()
            threading.Thread(target=run, daemon=True).start()

    with sd.InputStream(samplerate=SR, channels=1, dtype="float32", blocksize=BLOCK,
                        callback=lambda d, *_: ring.push(d[:, 0].copy())):
        print(f"hold {' / '.join(KEYS)} to talk (profile {PROFILE}, mode {MODE}, insert {INSERT}). ctrl-c to quit.")
        with keyboard.Listener(on_press=on_press, on_release=on_release) as L: L.join()


if __name__ == "__main__":
    main()

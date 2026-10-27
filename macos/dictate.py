#!/usr/bin/env python3
"""Bhavna.ai, macOS. Hold the key, speak Hindi / English / both, release. Your exact words land at the cursor.
Run: uv run --project macos macos/dictate.py
"""
import json, math, os, platform, queue, re, subprocess, sys, threading, time, wave
from collections import deque
from pathlib import Path
import numpy as np

PROFILE = os.environ.get("BHAVNA_PROFILE", "lean")   # lean = Apex only (~0.9 GB, English too) | full = tiny + Parakeet + Apex (~2.3 GB)  (ADR-012) | cascade = Swift + Apex + lazy Prime (ADR-015)
MODELS_FOR = {"lean": ("apex-mlx-q8",), "full": ("tiny-mlx", "parakeet-v2-mlx", "apex-mlx-q8"), "cascade": ("swift-mlx", "apex-mlx-q8", "prime-mlx-q8")}
WINDOW_SLACK_S, WINDOW_MAX_S = 1.0, 30   # Apex encoder window: clip + 1 s of silence, whole seconds, max 30 (ADR-012, bugs #88 #89)
MODE = "auto"              # auto | en | hinglish   (what a key does by default; lean ignores it, everything is Apex)
KEYS = {"alt_r": MODE}     # pynput key name -> mode. Two-key layout: {"alt_r": "en", "cmd_r": "hinglish"}
INSERT = "ax_then_paste"   # ax | paste | paste_shift | type | ax_then_paste   (owner's feel test, S5.0)
EN_THRESHOLD = 0.8         # tiny LID p(en) at or above this -> Parakeet, else Apex (ADR-002)
SR, BLOCK, PREROLL_S, POSTROLL_S, MIN_S = 16000, 1600, 0.5, 0.3, 0.3
# S3.4 transcribe while talking (ADR-013): cut chunks at pauses, transcribe in the background, insert once at release
PAUSE_S, MIN_CHUNK_S, MAX_CHUNK_S = 0.25, 4.0, 12.0     # cut after ≥ MIN_CHUNK_S when a pause ≥ PAUSE_S shows; force-cut at MAX_CHUNK_S
SPEECH_MIN_S, MARGIN_S = 1.0, 0.2    # a chunk needs ≥ SPEECH_MIN_S of speech before it is sent; trim margin around speech
CONTEXT_WORDS = 20         # previous chunk's last words go to the decoder as prompt (0 = off)
FALLBACK_LEFT_S, MIN_HISTORY_ROWS = 3.0, 30   # P3: guess for "talk time still to come" when his history is too short, and what "too short" means
# P4 cascade (ADR-015). RTF = decode seconds per audio second, M1. ponytail: GUESSES until T2.4 measures them on the M1; replace, do not trust
RTF = {"swift": 0.09, "apex": 0.46, "prime": 0.92}   # apex 0.46 = measured chunk p50 on 592 logged dictations; swift 0.2x and prime 2x of it are guesses
SLACK_Q = 0.1              # careful slack: the 10th percentile of talk time left, not the median (tools/simulate.py)
LAST_CHUNK_BUDGET_S, PRIME_MIN_TALK_S, PRIME_IDLE_S, RAM_FLOOR_MB = 0.7, 15.0, 300.0, 1024   # last-chunk decode budget | load Prime only for talks this long | unload after idle | never pick Prime under this free RAM
RESTORE_S = 1.5          # clipboard restore delay after a paste; a slow app reads the clipboard late (bug #97)
ROOT = Path(__file__).resolve().parents[1]
MODELS, STATS = ROOT / "models", ROOT / "stats.jsonl"
DICTIONARY = ROOT / "dictionary.tsv"   # S9.1: heard <TAB> correct <TAB> times <TAB> auto|ask; local only (ADR-014)
LOG_DIR = os.environ.get("LOG_DIR", str(ROOT / "log"))  # S8.1: on by default, local only; LOG_DIR="" turns it off
SOUNDS = ("/System/Library/Sounds/Tink.aiff", "/System/Library/Sounds/Bottle.aiff", "/System/Library/Sounds/Pop.aiff")  # start, stop (key up), done (text in)
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


def talk_history(path=STATS, min_rows=MIN_HISTORY_ROWS):
    """P3: talk lengths (audio_s) from his own stats. Under min_rows rows there is too little to trust: []."""
    try: rows = [json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]
    except OSError: return []
    xs = [r["audio_s"] for r in rows if "audio_s" in r]
    return xs if len(xs) >= min_rows else []


def expected_left(e, history, q=0.5):
    """P3: talk time still to come, given e seconds already talked: past talks longer than e, minus e. q = 0.5 is the median;
    a low q is a careful guess (ADR-015: the simulator showed the median makes Prime pile up a backlog)."""
    left = sorted(h - e for h in history if h > e)
    if not left: return FALLBACK_LEFT_S
    pos = q * (len(left) - 1); lo = int(pos)
    return left[lo] + (left[min(lo + 1, len(left) - 1)] - left[lo]) * (pos - lo)


def pick(len_s, backlog_s, e, history, free_mb, rtf=None):
    """P4: model for a chunk while he still talks. Prime if backlog + len*RTF fits the slack, else Apex, else Swift (ADR-015)."""
    rtf, slack = rtf or RTF, expected_left(e, history, SLACK_Q)
    if free_mb >= RAM_FLOOR_MB and backlog_s + len_s * rtf["prime"] <= slack: m = "prime"
    elif backlog_s + len_s * rtf["apex"] <= slack: m = "apex"
    else: m = "swift"
    return m, f"slack {slack:.1f}s backlog {backlog_s:.1f}s len {len_s:.1f}s free {free_mb}MB -> {m}"


def pick_last(len_s, rtf=None):
    """P4: the last chunk, at release: Apex only if it fits the budget, else Swift."""
    return "apex" if len_s * (rtf or RTF)["apex"] <= LAST_CHUNK_BUDGET_S else "swift"


def redo_with_prime(len_s, backlog_s, e, history, free_mb, rtf=None, released=False):
    """P4: a Swift-done chunk goes to Prime again only while he talks and Prime still fits."""
    return not released and pick(len_s, backlog_s, e, history, free_mb, rtf)[0] == "prime"


def load_dictionary(path=None):
    """S9.1: auto rows of dictionary.tsv as {heard (lowercase, single spaces): correct}. Missing file = {}. Read per dictation, so edits work at once."""
    p = Path(path or DICTIONARY)
    if not p.exists(): return {}
    out = {}
    for line in p.read_text().splitlines():
        f = line.split("\t")
        if line.startswith("#") or len(f) < 4 or f[3].strip() != "auto": continue
        out[" ".join(f[0].lower().split())] = f[1].strip()
    return out


def apply_dictionary(text, rules):
    """One pass, longest phrase first, whole words, any case and spacing: a swapped word is never swapped again. Returns (text, swaps)."""
    if not rules: return text, 0
    alts = "|".join(r"\s+".join(map(re.escape, k.split())) for k in sorted(rules, key=len, reverse=True))
    n = 0
    def swap(m):
        nonlocal n; n += 1; return rules[" ".join(m.group(0).lower().split())]
    return re.sub(rf"(?<!\w)(?:{alts})(?!\w)", swap, text, flags=re.I), n


def translated():
    return subprocess.run(["sysctl", "-n", "sysctl.proc_translated"], capture_output=True, text=True).stdout.strip() == "1"


def native(): return platform.machine() == "arm64" and not translated()  # ADR-008


def beep(i): subprocess.Popen(["afplay", "-v", str(SOUND_VOLUME), SOUNDS[i]])


def sample_len(seconds):
    """Decoder token cap from audio length (bug #96): Roman Hinglish ≈ 6 tokens/s; 8/s + 24 leaves margin, 440 is whisper's context."""
    return int(min(440, 24 + 8 * max(1, math.ceil(seconds))))


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
            if k > 2 or (k == 2 and L >= 4):                        # a 4+ word phrase said twice back to back is the model, not the speaker
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
    _win = np.hanning(BLOCK).astype(np.float32)
    _band = (np.fft.rfftfreq(BLOCK, 1 / SR) >= 300) & (np.fft.rfftfreq(BLOCK, 1 / SR) <= 3400)

    def __init__(self, sr=SR, block=BLOCK):
        self.sr, self.block, self.blocks, self.loud, self.floor = sr, block, [], [], None
        self.offset, self.bounds, self.quiet_run, self.rms_log, self.band_log = 0, [], 0, [], []

    def _is_speech(self, b):
        """Speech-band (300 to 3400 Hz) energy against a floor from the pre-roll, adapted by the quietest recent blocks.
        Bug #94: quiet built-in mic (floor 0.002, speech 0.008). Bug #99: hum/hiss input where full-band floor ≈ speech."""
        self.rms_log.append(float(np.sqrt(np.mean(b * b))))
        spec = np.abs(np.fft.rfft(b * self._win)); e = float(np.sqrt((spec[self._band] ** 2).sum() / self._band.sum()) / self.block * 2)
        self.band_log.append(e); n = len(self.band_log)
        if n <= 5: self.floor = float(np.median(self.band_log))         # pre-roll = room
        elif n % 10 == 0: self.floor = max(self.floor * 0.5, min(self.floor * 1.5, float(np.percentile(self.band_log[-30:], 5))))
        return e > max(2.0 * self.floor, 1e-4)

    def snr(self):
        """p90 / p5 of speech-band energy so far; under 3 means pauses may be missed."""
        if len(self.band_log) < 20: return None
        return round(float(np.percentile(self.band_log, 90) / max(np.percentile(self.band_log, 5), 1e-6)), 1)

    def push(self, b):
        sp = self._is_speech(b); self.blocks.append(b); self.loud.append(sp)
        self.quiet_run = 0 if sp else self.quiet_run + 1
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
        # Trim only leading room noise, at most 1 s, and only when the mic is clearly separable (bugs #94, #99).
        # Never trim the tail: the next chunk starts exactly where this one ends, so no audio can fall between chunks.
        m, cap = int(MARGIN_S * self.sr / self.block), int(1.0 * self.sr / self.block)
        lo = max(0, first - m, first - cap) if (first > m and (self.snr() or 0) >= 5) else 0
        hi = n_blocks
        chunk = np.concatenate(blocks[lo:hi])
        self.bounds.append({"start_s": round((self.offset + lo * self.block) / self.sr, 2),
                            "end_s": round((self.offset + hi * self.block) / self.sr, 2), "speech_s": round(speech_s, 2), "kind": kind})
        self.offset += n_blocks * self.block
        self.blocks, self.loud = self.blocks[n_blocks:], self.loud[n_blocks:]
        self.quiet_run = 0
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


class LazyModel:
    """P5: loads on first get(), drops after idle_s without use (Prime is 1.5 GB: only resident while it earns it)."""
    def __init__(self, loader, idle_s=None, clock=time.monotonic):
        self.loader, self.idle_s, self.clock, self.model, self.used = loader, PRIME_IDLE_S if idle_s is None else idle_s, clock, None, 0.0
    def get(self):
        if self.model is None: self.model = self.loader()
        self.used = self.clock(); return self.model
    def unload_if_idle(self):
        if self.model is not None and self.clock() - self.used > self.idle_s: self.model = None


def free_ram_mb(vm_stat_text=None):
    """P5: MB the Mac can hand out now = free + inactive + speculative pages, from vm_stat."""
    t = vm_stat_text or subprocess.run(["vm_stat"], capture_output=True, text=True).stdout
    page = int(re.search(r"page size of (\d+)", t).group(1))
    pages = sum(int(m.group(1)) for k in ("free", "inactive", "speculative") if (m := re.search(rf"Pages {k}:\s+(\d+)", t)))
    return pages * page // 2**20


class Cascade:
    """P5 (ADR-015): fn(audio, prompt, e, queued_s, released) -> text. pick() chooses; every choice goes to .log."""
    def __init__(self, models, prime_loader, history, rtf=None, free_mb=free_ram_mb, clock=time.monotonic):
        self.models, self.prime, self.history, self.rtf, self.free_mb, self.log = models, LazyModel(prime_loader, clock=clock), history, rtf or RTF, free_mb, []
    def __call__(self, a, prompt=None, e=0.0, queued_s=0.0, released=False):
        n = len(a) / SR
        if released: m, why = pick_last(n, self.rtf), "release: last-chunk budget"
        else:
            m, why = pick(n, queued_s * self.rtf["apex"], e, self.history, self.free_mb(), self.rtf)
            if m == "prime" and self.prime.model is None and e < PRIME_MIN_TALK_S: m, why = "apex", why + " (talk too short to load prime)"
        self.log.append({"model": m, "reason": why})
        fn = self.prime.get() if m == "prime" else self.models[m]
        self.prime.unload_if_idle()
        return fn(a, prompt=prompt)
    def counts(self):
        out = {}
        for x in self.log: out[x["model"]] = out.get(x["model"], 0) + 1
        return out


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

        opts = DecodingOptions(language="en", task="transcribe", without_timestamps=True, temperature=0.0, fp16=True)

        def build(model):   # one Whisper-family MLX model -> fn(audio, prompt) -> text (same decode for Swift, Apex, Prime)
            def one(a, o=opts):
                w = window_s(len(a) / SR)
                mel = pad_or_trim(log_mel_spectrogram(a, n_mels=model.dims.n_mels, padding=max(0, w * SR - len(a))), w * 100, axis=-2).astype(mx.float16)
                o = DecodingOptions(**{**o.__dict__, "sample_len": sample_len(len(a) / SR)})
                return decode(model, mel, o).text.strip()

            def hinglish(a, prompt=None):
                o = DecodingOptions(language="en", task="transcribe", without_timestamps=True, temperature=0.0, fp16=True, prompt=prompt) if prompt else opts
                return " ".join(t for t in (one(p, o) for p in pieces(a)) if t)
            return hinglish

        hinglish = build(load_model(str(MODELS / "apex-mlx-q8"), dtype=mx.float16))
        self.hinglish, self.lid, self.en = hinglish, None, None
        warm = np.zeros(SR, np.float32); hinglish(warm)
        if profile == "cascade":   # Prime (1.5 GB) loads later, only for long talks (ADR-015)
            self.swift = build(load_model(str(MODELS / "swift-mlx"), dtype=mx.float16)); self.swift(warm)
            self.prime_loader = lambda: build(load_model(str(MODELS / "prime-mlx-q8"), dtype=mx.float16))
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
    threading.Timer(RESTORE_S, restore).start()
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
    st = {"q": None, "out": None, "chunker": Chunker(), "route": None, "t_down": 0.0, "queued_s": 0.0, "released": False}
    cas = Cascade({"swift": m.swift, "apex": m.hinglish}, m.prime_loader, talk_history()) if PROFILE == "cascade" else None   # history read once, at start-up

    def start(mode):
        st["q"], st["out"], st["chunker"] = queue.Queue(), WorkerOut(), Chunker()
        st["route"], st["t_down"], st["queued_s"], st["released"] = RouteOnce(m, mode, PROFILE), time.perf_counter(), 0.0, False
        if cas: cas.log = []
        def fn(a, prompt=None):
            if cas:   # ADR-015: the cascade picks swift / apex / prime for this chunk
                st["queued_s"] -= len(a) / SR
                return cas(a, prompt, e=time.perf_counter() - st["t_down"], queued_s=max(0.0, st["queued_s"]), released=st["released"])
            return (m.en if st["route"](a) == "en" else m.hinglish)(a, prompt=prompt)
        threading.Thread(target=run_worker, args=(st["q"], fn, st["out"]), daemon=True).start()
        ring.start(); beep(0)

    def on_block(b):
        ring.push(b)
        if ring.rec is not None and st["q"] is not None:
            for c in st["chunker"].push(b): st["queued_s"] += len(c) / SR; st["q"].put(c)

    def finish(t_up):
        time.sleep(POSTROLL_S)  # keep the last syllable spoken as the key comes up
        a = ring.stop(); q, out, ch = st["q"], st["out"], st["chunker"]; st["q"] = None
        st["released"] = True   # from here every chunk left is on the critical path (cascade uses the last-chunk budget)
        last = ch.flush(final=True); t_final_q = time.perf_counter()
        if last is not None: st["queued_s"] += len(last) / SR; q.put(last)
        q.put(None); out.done.wait()
        if too_short(a) or not out.items: print(f"dropped ({len(a) / SR:.1f}s)"); return
        raw = " ".join(r["text"] for r in out.items if r["text"]); r = st["route"].r or "hinglish"
        text, swaps = apply_dictionary(raw, load_dictionary())
        t0 = time.perf_counter(); how = insert(text, kb) if text else "empty"; t1 = time.perf_counter()
        beep(2)
        fin = out.items[-1]; wait_ms = max(0.0, (fin["t_start"] - t_final_q) * 1000) if last is not None else 0.0
        rel = (t1 - t_up) * 1000; asr_total = sum(x["ms"] for x in out.items); audio_s = len(a) / SR
        kinds = [bd["kind"] for bd in ch.bounds]
        print(f"[{time.strftime('%H:%M:%S')}] {r:8} {len(out.items)} chunks  release→text {rel:4.0f}ms (wait {wait_ms:.0f} final {fin['ms']} insert {(t1 - t0) * 1000:.0f}) {how}  \"{text}\"")
        row = dict(route=r, release_to_text_ms=round(rel), postroll_ms=round(POSTROLL_S * 1000), wait_ms=round(wait_ms), final_asr_ms=fin["ms"],
                   insert=how, insert_ms=round((t1 - t0) * 1000), asr_total_ms=asr_total, rtf=round(asr_total / (audio_s * 1000), 3),
                   chunks=len(out.items), pause_cuts=kinds.count("pause"), forced_cuts=kinds.count("forced"),
                   audio_s=round(audio_s, 2), speech_s=round(sum(bd["speech_s"] for bd in ch.bounds), 2), errors=out.errors, repeats=out.repeats, dict_swaps=swaps, profile=PROFILE)
        if cas: row["models"] = cas.counts()
        stats(STATS, text, **row)
        stem = time.strftime("%Y%m%d-%H%M%S")
        meta = {**row, "profile": PROFILE, "constants": dict(PAUSE_S=PAUSE_S, MIN_CHUNK_S=MIN_CHUNK_S, MAX_CHUNK_S=MAX_CHUNK_S, CONTEXT_WORDS=CONTEXT_WORDS, WINDOW_SLACK_S=WINDOW_SLACK_S),
                "t_down_to_up_s": round(t_up - st["t_down"], 2), "chunks_detail": [{**bd, **{k: it[k] for k in ("text", "ms")}, **lg} for bd, it, lg in zip(ch.bounds, out.items, cas.log if cas else [{}] * len(out.items))], "raw_text": raw, "text": text}
        log_dictation(LOG_DIR, stem, a, text, meta)
        if cas: t = threading.Timer(PRIME_IDLE_S + 1, cas.prime.unload_if_idle); t.daemon = True; t.start()   # give Prime's 1.5 GB back after idle

    def on_press(k):
        if k in keys and ring.rec is None and not busy.locked(): start(keys[k])

    def on_release(k):
        if k in keys and ring.rec is not None and busy.acquire(blocking=False):
            t_up = time.perf_counter(); beep(1)
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

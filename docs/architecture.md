# Architecture and research summary

<!-- Source: docs/PLAN.md. Edit there, then re-split. -->

### B1. Research summary (tiers per the house web-research rules; confidence 0 to 1)

**Root cause of the Hindi penalty.** Devanagari costs about 4.7 tokens per word; English about
1.0 to 1.3; Romanized Hindi about 1.7 to 2.0. One token is one decoder step (about 15 ms). Hindi
is about 2.5x English. Sources: a WhisperKit maintainer's measured issue (Tier P) and an ICASSP 2025
paper (Tier A). Confidence 0.9.

**Hinglish model: Oriserve Whisper-Hindi2Hinglish-Apex.** Tier B (vendor; public weights and WER).
Verified from its `config.json`: whisper-large-v3-turbo architecture (32 encoder / 4 decoder
layers, 128 mel), 0.8 B params, `model.safetensors` 1.62 GB fp16, Apache 2.0. About 700 h of
Indian-accented Hindi. Roman output with `language="en"`. FLEURS-hi WER 29.8 vs 50.8 base
(confidence 0.6 until our own test). GGML builds exist (q5 547 MB, q8 834 MB). No MLX or CT2 build;
we convert once.
Rejected: Trelis (Devanagari for Hindi, 2 B). Oriserve Swift (whisper-base, weak; kept only for
the micro profile). Voxtral Mini 3 B (RAM). IndicConformer (NeMo stack, Devanagari).

**English model: Parakeet-TDT-0.6B-v2.** Open ASR leaderboard about 6.05 WER vs 7.8 for turbo
(Tier A). About 2x faster than mlx-whisper on Apple Silicon (Tier P, M4). English only. parakeet-mlx
loads from a local folder (verified in source). onnx-asr on Windows, int8, local dir; runs a
production service on 2 vCPU / 2 GB (Tier P); 5 to 8x realtime on a laptop CPU (Tier C).

**Router.** whisper-tiny `detect_language` exists in mlx-whisper and faster-whisper (verified in
source). About 75 MB, about 50 ms on M1. Threshold p(en) ≥ 0.8 sends to Parakeet, else Apex. Fails
safe, because Apex also handles Indian English. Accuracy on Indian accents is unmeasured,
confidence 0.5, so it has a Phase 0 gate.

**macOS engine.** mlx-whisper is 2.0x faster than whisper.cpp Metal on turbo (Tier P, Jan 2026).
Takes an ndarray and a local path; caches the model; pads to 30 s. Must override: the temperature
tuple, `condition_on_previous_text`, three retry thresholds. The conversion script lives in
mlx-examples and needs torch; one-time. RAM: turbo q8 about 2.3 GB peak, q4 about 1.5 GB (Tier B).

**Windows engine.** faster-whisper (CT2, `device="auto"`) vs pywhispercpp (whisper.cpp,
`audio_ctx=768` cuts the 30 s window, about 3x faster at 512, Tier A docs). CPU sub-second is not
promised (confidence 0.4). Decided by the Phase 0 gate.

**Insertion.** FluidVoice source (Tier A): AX `kAXSelectedTextAttribute` set, paste fallback,
clipboard restore. whispr-bro spec: concealed pasteboard type, changeCount-checked restore. Handy
(Tier A): clipboard plus enigo paste cross-platform. Wispr Flow (Tier C): Accessibility insertion,
Fn hold, p90 and p99. pynput's mac dependencies already include pyobjc ApplicationServices and
Quartz, so AX costs nothing extra. Keep the mic stream open with a 500 ms pre-roll ring buffer; warm
models at start.

**Hugging Face.** HF is a file host; repos are plain files; nothing is renamed or bloated; only its
downloader creates the cache layout. We never call it at run time. No token needed. Remaining risk:
PyPI blocked on the company laptop, mitigated by an optional `wheels/` folder in the zip.

**Rosetta.** Ends at macOS 28 (Tier A). User zero's Mac verified fully arm64 today (python3, uv
Pythons, Homebrew, ffmpeg, `proc_translated` = 0). Rules in ADR-008.

**Hardware floor.** Mac floor = M1 8 GB (user zero's machine; Intel Macs excluded). Windows floor =
4 GB CPU-only: Parakeet int8 is fine; Hinglish via Apex q5 plus `audio_ctx` (8 GB) or Swift (4 GB).
One whisper engine per OS, chosen by measurement.

**Fine-tuning data.** HiACC 5.2 h real code-switched, Zenodo (Tier A). IndicVoices Hindi 447 h,
CC BY 4.0, half the code-switched words carry Latin spelling (Tier A). IITG-HingCoS 25 h.
agarwalayushi/hinglish 2,264 h CC BY 4.0 but merged and partly synthetic, script unstated (Tier C).
The user's own log is S-tier and best. LoRA r=32 on Apex: about 2.5 h and about $15 on an A10G for
5.8 h of audio (Tier P).

### B2. Architecture

```
            ┌──────────────── dictate.py (one process, one thread + audio callback) ────────────────┐
 key ──▶ pynput listener ──▶ recording flag ──▶ ring buffer (sounddevice callback, always on, 500 ms pre-roll)
                                                     │ key up → np.ndarray (16 kHz mono f32)
                                                     ▼
                                           whisper-tiny detect_language  (~50 ms)
                                              │ p(en) ≥ 0.8        │ else
                                              ▼                    ▼
                                     Parakeet v2 (resident)   Apex turbo (resident, lang=en, greedy)
                                              └────────┬───────────┘
                                                       ▼ text
                                        insert: AX set → (error) → concealed clipboard + ⌘V + restore
                                                       ▼
                                           stdout: one line with timings
```
Mac: MLX for all three models. Windows: onnx-asr (Parakeet) plus faster-whisper or pywhispercpp
(by gate). Models are folders in `models/`; the script never downloads.

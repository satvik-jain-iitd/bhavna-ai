# Research findings: models, engines, insertion (2026-10-07)

Tiers: A primary (code, config, paper, platform doc), B seller data with method, C blog or vendor
claim, P named person with evidence, S owner's own data. Confidence 0 to 1. Rows are never deleted;
outdated rows get marked.

| # | Claim | Evidence | Tier | Conf. | What it changes |
|---|---|---|---|---|---|
| 1 | Whisper decodes Devanagari at ~4.7 tokens/word vs ~1.0 to 1.3 English, ~1.7 to 2.0 Romanized; Hindi ≈ 2.5x latency | [WhisperKit maintainer issue, measured on M5 Pro](https://github.com/uttrflow/uttrflow-swift/issues/962); [ICASSP 2025 paper on Indic tokenization](https://arxiv.org/abs/2412.19785) | P, A | 0.9 | ADR-001: Roman output only |
| 2 | Oriserve Apex is whisper-large-v3-turbo architecture (32 enc / 4 dec, 128 mel), 0.8 B, 1.62 GB fp16, Apache 2.0, Roman output with `language="en"` | [config.json](https://huggingface.co/Oriserve/Whisper-Hindi2Hinglish-Apex/raw/main/config.json); [model card](https://huggingface.co/Oriserve/Whisper-Hindi2Hinglish-Apex) (vendor) | A (config), B (WER) | 0.9 / 0.6 | Hinglish model choice |
| 3 | Apex FLEURS-hi WER 29.8 vs 50.8 base large-v3 | model card, vendor numbers | B | 0.6 | needs own test (experiments H2) |
| 4 | Oriserve Swift = whisper-base fine-tune, 72 M, WER 35 to 65 | [model card](https://huggingface.co/Oriserve/Whisper-Hindi2Hinglish-Swift) | B | 0.7 | micro profile only |
| 5 | Trelis whisper-hinglish writes Devanagari for Hindi, 2 B | [model card](https://huggingface.co/Trelis/whisper-hinglish-preview) | B | 0.8 | rejected |
| 6 | Parakeet-TDT-0.6B-v2 ~6.05 WER vs whisper-turbo 7.8 on Open ASR leaderboard; English only | [leaderboard summary](https://www.codesota.com/benchmark/open-asr-leaderboard); [Parakeet v3 paper](https://arxiv.org/pdf/2509.14128) | A | 0.85 | English model choice |
| 7 | parakeet-mlx ~0.50 s vs mlx-whisper turbo ~1.02 s per sample on M4; FluidAudio CoreML 0.19 s (Swift) | [mac-whisper-speedtest](https://github.com/anvanvan/mac-whisper-speedtest) | P | 0.75 | Parakeet for English; CoreML noted as faster but Swift |
| 8 | mlx-whisper 2.0x faster than whisper.cpp Metal on large-v3-turbo | [billmill benchmark, Jan 2026](https://notes.billmill.org/dev_blog/2026/01/updated_my_mlx_whisper_vs._whisper.cpp_benchmark.html) | P | 0.8 | ADR-003 |
| 9 | whisper turbo RAM: fp16 3.6 GB, q8 2.3 GB, q4 1.5 GB peak on M1 | [OpenASR table](https://huggingface.co/OpenASR/whisper-large-v3-turbo) | B | 0.7 | fits 8 GB; q4 fallback |
| 10 | mlx_whisper.transcribe takes ndarray and a local path; caches model; pads to 30 s; default temperature tuple and thresholds cause retries | [transcribe.py](https://raw.githubusercontent.com/ml-explore/mlx-examples/main/whisper/mlx_whisper/transcribe.py) | A | 0.95 | decode options in dictate.py |
| 11 | mlx_whisper.decoding.detect_language(model, mel) exists and runs the encoder | [decoding.py](https://raw.githubusercontent.com/ml-explore/mlx-examples/main/whisper/mlx_whisper/decoding.py) | A | 0.95 | router |
| 12 | faster-whisper WhisperModel.detect_language(audio) returns (lang, prob, all) | [transcribe.py](https://raw.githubusercontent.com/SYSTRAN/faster-whisper/master/faster_whisper/transcribe.py) | A | 0.95 | Windows router |
| 13 | parakeet-mlx from_pretrained falls back to a local dir with config.json + model.safetensors | [utils.py](https://raw.githubusercontent.com/senstella/parakeet-mlx/master/parakeet_mlx/utils.py) | A | 0.9 | bundled weights |
| 14 | onnx-asr loads nemo-parakeet-tdt-0.6b-v2 from a local dir, int8, numpy input; 36x RTF on a desktop CPU | [usage docs](https://istupakov.github.io/onnx-asr/usage/); [README](https://github.com/istupakov/onnx-asr) | A, B | 0.8 | Windows English path |
| 15 | Parakeet v2 int8 runs a production service on 2 vCPU / 2 GB | [letsdatascience report](https://letsdatascience.com/news/parakeet-outperforms-whisper-on-low-cost-cpu-deployment-de238707) | P | 0.6 | floor hardware |
| 16 | whisper.cpp audio_ctx=512 ≈ 3x faster on short audio, some quality loss | whisper.cpp docs via [whisper.rn tips](https://www.mintlify.com/mybigday/whisper.rn/resources/tips-and-tricks) | A | 0.8 | lean profile |
| 17 | FluidVoice inserts via AX set, falls back to Cmd+V, restores clipboard; rejects keystroke events for terminals, IDEs, IMEs | [FluidVoice repo](https://github.com/altic-dev/FluidVoice) (TypingService.swift) | A | 0.9 | ADR-005 |
| 18 | Wispr-Flow clone spec: concealed pasteboard type, changeCount-checked restore, 500 ms pre-roll ring buffer, Parakeet ~190 to 250 ms on ANE | [whispr-bro spec](https://github.com/Micaxes/whispr-bro/issues/1) | C | 0.6 | pre-roll, restore |
| 19 | Wispr Flow: Accessibility permission for insertion, hold Fn, measures p90/p99 | [field guide](https://github.com/vkorost/wispr-flow-field-guide/blob/main/book/chapters/04-macos.md) | C | 0.5 | p90 metric; permission does not reveal method |
| 20 | Handy pastes via clipboard + enigo cross-platform | [Handy](https://github.com/cjpais/Handy) | A | 0.8 | Windows insert |
| 21 | pynput segfaults on macOS 26 + Python 3.14 | [Klaus troubleshooting](https://mintlify.wiki/bgigurtsis/klaus/troubleshooting/macos-permissions) | C | 0.6 | pin Python < 3.14 |
| 22 | Rosetta ends for general apps at macOS 28 | [Apple 102527](https://support.apple.com/en-gb/102527) | A | 0.95 | ADR-008 |
| 23 | Hinglish data: HiACC 5.2 h real code-switched (Zenodo); IndicVoices Hindi 447 h CC BY 4.0 with Latin spelling for half the code-switched words; agarwalayushi/hinglish 2,264 h merged, partly synthetic | [HiACC](https://pmc.ncbi.nlm.nih.gov/articles/PMC12329218/); [hinglish-audio-dataset](https://github.com/ayushi-agarwall/hinglish-audio-dataset) | A, C | 0.7 / 0.4 | fine-tune plan |
| 24 | LoRA fine-tune of whisper turbo on 5.8 h Hindi: ~2.5 h, ~$15 on A10G | [annotehrushi model card](https://huggingface.co/annotehrushi/whisper-large-v3-turbo-hindi) | P | 0.6 | fine-tune cost |
| 25 | "Ease" UI repo: not found by search | web search 2026-10-07 | - | - | owner to share link |
| 26 | Wispr Flow: text after release; p99 < 700 ms = ASR < 200 + LLM < 200 + network 200; ASR runs during capture; "every edit after the fact adds more time" | [Wispr technical post](https://wisprflow.ai/post/technical-challenges); [Baseten case study](https://www.baseten.co/resources/customers/wispr-flow/) (vendor) | A | 0.8 | ADR-013 shape: transcribe while talking, one insert |
| 27 | FluidAudio: true streaming Parakeet EOU 120 M + Silero VAD (256 ms hop) + end-of-utterance; 4.87 WER at 320 ms; English only | [FluidAudio](https://github.com/FluidInference/FluidAudio) | A | 0.85 | S4.4 follow-up for the full profile |
| 28 | whisper.cpp stream: fixed-step re-decode or VAD sliding window; previous tokens as prompt; VAD "very basic" | [stream README](https://huggingface.co/datasets/echodict/whisper.cpp/blob/main/examples/stream/README.md) | A | 0.9 | pause-chunk + prompt tail |
| 29 | LocalAgreement-2 (ufal whisper_streaming) / WhisperKit Eager: re-decode growing buffer, commit agreed prefix; 3.3 s latency | [paper](https://arxiv.org/html/2307.14743); [WhisperKit issue](https://github.com/argmaxinc/WhisperKit/issues/102) | A | 0.9 | rejected: double compute, slower |
| 30 | Endpointing: Deepgram default 10 ms, example 300 ms, UtteranceEnd ≥ 1000 ms; Silero min silence 100 ms, min speech 250 ms; 50 to 100 ms splits sentences, 300 to 1000 whole sentences | [Deepgram](https://developers.deepgram.com/docs/endpointing); Silero defaults via vendor docs | A | 0.8 | PAUSE_S 0.25 for chunk boundaries only; MIN_SPEECH_RUN_S 0.25 |
| 31 | Market scan: VoiceInk Pro live text (cloud); Superwhisper, Wispr after stop; quoted latencies Willow 190 ms, Wispr 400, Superwhisper 480, Typeless 900 | vendor comparison pages | C | 0.4 | direction only |

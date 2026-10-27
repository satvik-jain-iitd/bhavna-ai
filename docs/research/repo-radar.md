# Repo radar runs (append only)

## 2026-10-27: multi-model ASR cascade scheduler (issue #109)

**Need:** multi-model ASR cascade scheduler with latency budget for chunked dictation.

**Runs:**
- `scout.py --need "<need>"`: "no repos found".
- GitHub `topic:` search (`whisper-streaming`, `speech-recognition`, `local-agreement`): 1 weak hit (4 stars, a faster-whisper websocket demo).
- Named-repo health check with `gh repo view`.

**Top 3 READMEs read:**
| Repo | Stars | Last push | Verdict |
|---|---|---|---|
| ufal/whisper_streaming | 3675 | 2025-11-12 | Outdated by its own README. Borrow the idea: LocalAgreement, commit text only when two runs agree. Does not pick between models. |
| QuentinFuxa/WhisperLiveKit | 11182 | 2026-10-23 | Live server with VAD and streaming policies. It streams one model. No slack-based model choice. Do not adopt: GUI/server, streaming is out of scope (ADR-010). |
| ufal/SimulStreaming | 692 | 2026-07-12 | AlignAtt policy for simultaneous output, aimed at GPUs. Not for an 8 GB M1. Ideas only. |

**Result:** nothing schedules several ASR models by slack. The pick rule `pick()` is new code (about 20 lines of pure function).
**Borrow:** LocalAgreement as a later option for idea (b), the speculative final decode. Nothing for P3 or P4.
**Build from scratch:** the scheduler and `expected_left`. Reason: the run found nothing that fits. Run path: this file.

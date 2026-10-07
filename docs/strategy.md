# Product strategy

<!-- Source: docs/PLAN.md. Edit there, then re-split. -->

### A1. Product strategy

**Vision.** Anyone in India can talk to their computer the way they really speak, Hindi and English
mixed, and see their exact words appear at the cursor in under a second, on the cheapest machine
they own, with nothing leaving the device.

**Mission for v1.** A dictation engine on user zero's own Mac that is faster and more faithful for
Hinglish than any paid tool, with no feature beyond push-to-talk and insert.

**Why now.**
- Open models now beat the paid clouds on English (Parakeet v2, about 6% word error rate), and a
  Roman-Hinglish fine-tune of Whisper exists under a permissive licence (Oriserve Apex, Apache 2.0).
- Apple Silicon runs these models from memory on an 8 GB laptop. Cheap x86 CPUs run int8 ONNX.
- Paid tools (Wispr Flow, Superwhisper) optimise for English and add LLM cleanup that Hinglish
  speakers do not want. Their Hindi path is 2.5x slower for a structural reason (the tokenizer)
  that none of them has fixed.
- Most typing now happens in LLM chat boxes. LLMs tolerate small spelling slips. A fast, faithful
  transcript beats a slow, polished one.

**Wedge.** Hinglish speed. Every competitor pays the Devanagari token tax. We route around it.

**Positioning.** "The dictation engine, not the dictation app." Pass-through only. No rewriting, no
summaries, no tray icon. Works offline. Ships as one zip with the weights inside.

**Non-goals for v1.** Devanagari output. Streaming partial text. LLM cleanup. GUI. Cloud sync.
Mobile. Languages beyond English, Hindi and their mix.

**The accuracy bar, stated plainly.** We do not target 100% accuracy in v1. A reader or an LLM
must understand exactly what was meant; a few spelling or grammar slips are acceptable. 80 to 85%
word accuracy is a fine starting point. This is a deliberate difference from Wispr Flow's CTO, who
wants everything correct. Our view: speed and faithfulness first; the personal dictionary (A8,
E9) closes the gap over time, word by word, using the user's own corrections. If the dictionary is
not enough, the user's own data trains a better model (E10). That is the last option, not the
first. First make it exist, even slightly ugly, but working.

**Success metrics.** Each row says what we want to know, how we capture it today, and what we
would need if we cannot capture it yet. A metric we cannot capture is still written down.
| Metric | Target (v1, user zero's M1 8 GB) | How captured |
|---|---|---|
| Key release to text inserted, English | p50 < 0.7 s, p90 < 1.0 s | every dictation appends one row to a local `stats.jsonl` (timestamp, route, stage ms, word count, audio seconds); bench.py for fixtures |
| Same, Hinglish | p50 < 1.2 s, p90 < 1.6 s | same |
| Hinglish penalty vs English | < 1.6x (today's tools: 2.5x) | same |
| Daily use | five working days with no alternative dictation app opened (user zero uses FluidVoice today) | `stats.jsonl` row count per day; ActivityWatch (already installed) for time in other apps; FluidVoice detection: ActivityWatch sees it only when its window is focused, so also a daily `pgrep FluidVoice` check written to the journal |
| Words dictated per day | trend up over 4 weeks | `stats.jsonl` word counts |
| Time saved per day | reported, no target in v1 | words × (1/40 typing wpm − 1/130 speaking wpm), from `stats.jsonl`; assumption stated |
| Insert success | 100% in TextEdit, Chrome, VS Code, Terminal, Slack | acceptance matrix |
| Resident RAM | < 2.5 GB on an 8 GB machine | /usr/bin/time -l |
| Privacy | zero network calls after install | tcpdump over a 10-minute session |
| Is the tool improving itself (v3) | corrections per 100 words trend down; dictionary hits per week trend up | the dictionary helper logs each swap and each learned word to `stats.jsonl` |

**Business model (not now).** Open-source core. Possible later: paid personal fine-tune, paid team
dictionary sync. Written down so the architecture does not block it. Not built.

### A8. Roadmap (what stays in scope after v1)

| Version | Scope | Why it is on the roadmap |
|---|---|---|
| v1 | One key, two models, auto-route, sounds, insert, zip, stats log. Mac. | make it exist for user zero |
| v2 | Windows build on the company laptop; profiles for CPU-only machines; insertion feel test result locked in | the second machine user zero owns; P2 |
| v3 | **Self-improvement dictionary** (E9): applied at dictation time, learned from the user's own corrections, all local. Opt-in data log (E8). | the accuracy gap in v1 is closed by the dictionary, not by a bigger model. This feature stays in scope in every roadmap revision |
| v3 | Secure-field refusal; optional tray icon or overlay if the owner wants it after the feel test | small polish, only if asked |
| v4 | Fine-tune on the user's own data plus public Hinglish sets (E10). Owner is open to building his own dataset if it comes to that. | last option, after the dictionary; a model that starts somewhere and improves from daily input |
| later | micro profile on 4 GB machines (P3); auto hardware detection; Indic-tokenizer models when they appear | the "cheapest device, best speed" vision |

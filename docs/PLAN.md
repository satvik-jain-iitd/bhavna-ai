# Bhavna.ai: Product Plan and Case Study

> "Main sochta Hindi mein hoon, kaam English mein karta hoon, aur bolta dono mila ke hoon.
> Jab main Hindi bolta hoon, dictation tool ruk jaata hai. Jab text aata hai, usne mere shabd
> badal diye hote hain. Office laptop par toh chalta hi nahi. Mujhe bas itna chahiye: main boloon,
> mere hi shabd, usi jagah, turant."
>
> "I think in Hindi, I work in English, and I speak both mixed together. When I speak Hindi, the
> dictation tool stalls. When the text arrives, my words have been changed. On the office laptop it
> does not run at all. I want one thing: I speak, my own words, at the cursor, right now."

This is the user we build for: the bilingual Indian knowledge worker. Tens of millions of people
type Roman Hindi on WhatsApp every day and then switch to English for work, often inside the same
sentence. Every dictation tool on the market makes them choose a language, pay a speed penalty for
Hindi, and accept an LLM rewriting what they said.

Satvik, the owner of this project, is one of these users. He tested FluidVoice, Musely and
Superwhisper for his own daily work, hit the Hindi lag, hit the rewriting, hit the locked-down
company laptop, and decided to build the tool he could not buy. He is user zero: the first person
to use every build, the first to measure it, and the first to be annoyed by it. The plan below is
written for the user above, and tested on Satvik's own two machines first.

This file is the plan and the case study. It shows the product thinking (who, why, what, what not),
the engineering thinking (research, architecture, decisions, trade-offs, risks), the backlog
(epics, stories, acceptance criteria), and the process (how the work runs on GitHub with
test-driven development, demos at every step, and a written journey).

How to read it:
- Part A: product. Strategy, market, industry, users, experience, requirements, MVP.
- Part B: engineering. Research, architecture, decision records, risks.
- Part C: backlog. Epics and stories with Gherkin acceptance criteria.
- Part D: process. GitHub, branches, TDD, demos, journal, definitions of done.

When execution starts, this file is copied to the repo as `docs/PLAN.md` and then split into the
`docs/` tree. The repo copy becomes the single source of truth and this file points to it.

---

## Part A: Product

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

### A2. Market and competitor research

Sources are vendor pages and open-source repos. Vendor claims are Tier C unless the code is open
(Tier A for the mechanism). Latency numbers are theirs unless marked.

| Product | Runs | Price | Hindi / Hinglish | Insert method | Bloat | Open |
|---|---|---|---|---|---|---|
| Wispr Flow | cloud ASR, mac/win | $12/mo | Hindi yes; Roman output not documented | Accessibility API | LLM cleanup always on | no |
| Superwhisper | local whisper + cloud, mac | $8.49/mo or $249 | Hindi via whisper, Devanagari, slow | paste | AI modes, GUI | no |
| FluidVoice | local (Parakeet CoreML, WhisperKit), mac | free | Parakeet v3 has no Hindi; whisper path is Devanagari | AX set + paste fallback (code read) | LLM "Fluid-1" polish, menu bar | GPLv3 |
| VoiceInk | local, mac | $25 once or build free | whisper, Devanagari | paste | AI enhancement, GUI | yes |
| Handy | local (whisper, Parakeet), mac/win/linux | free | whisper, Devanagari | clipboard paste (enigo) | Tauri GUI | MIT |
| OpenWhispr | local + cloud, cross | free | whisper, Devanagari | paste | Electron GUI | MIT |
| Musely | cloud, mac | subscription | Hindi slow (user zero's test) | paste | GUI, AI | no |
| macOS / Windows built-in | local or cloud | free | Hindi yes, Devanagari, no Hinglish | native | none | no |
| Gboard voice (phone) | cloud or on-device | free | Hinglish OK | native | none | no |

What every row shares: Hindi means Devanagari, and Devanagari means the token tax. None ships a
Roman-Hinglish model. None bundles weights for locked-down laptops. Most add an LLM pass the user
cannot fully switch off.

What we borrow: AX insertion with paste fallback (FluidVoice), hold-to-talk on one key (Wispr),
Parakeet for English (FluidVoice, Handy), p90 as the number that matters (Wispr's CTO).

### A3. Industry research (what is moving under this product)

- **Models are getting smaller and better.** A 0.6 B model (Parakeet) now beats a 1.5 B model
  (whisper-large) on English. Expect the same for Indic within a year (AI4Bharat, Oriserve, Sarvam
  are all publishing). Architecture rule: a model is a folder in `models/`, swappable.
- **Tokenizer cost is the hidden Indic bottleneck.** Papers (ICASSP 2025) and maintainers (a
  WhisperKit issue) both measure about 2.5x. Expect Indic-tokenizer models soon. Until then, Roman
  output.
- **On-device is the default for sensitive work.** Company laptops block cloud AI and Hugging Face.
  Bundled weights are a feature, not a workaround.
- **Apple Silicon only, going forward.** Rosetta ends at macOS 28 (Apple article 102527). Intel Mac
  support is dead weight. MLX is the Apple-native Python path; CoreML on the Neural Engine is faster
  still but Swift-only.
- **Windows is a CPU story for most Indian laptops.** The cheapest machines have 4 to 8 GB and an
  integrated GPU. int8 ONNX and whisper.cpp's shortened encoder window are the tools that fit.
- **Code-switched speech is an open research gap.** Public Hinglish data is small (HiACC, 5 h) or
  synthetic. A user's own corrections are the most valuable data. That is the self-learning lever.

### A4. Users: personas, jobs, prioritisation

**P1. The bilingual knowledge worker (primary, v1).** Works in India, writes into Claude, Slack,
docs and WhatsApp Web all day. Speaks Hinglish without thinking about it. Owns an M-series Mac or a
mid-range Windows laptop at home and a locked-down laptop at work. Has paid for tools and dropped
them for speed. Job: "When I have a thought, get it into the box in front of me before I lose it,
in the words I said." Pain: the Hindi lag breaks the flow, tools rewrite the words, nothing runs on
the work laptop. Success: they stop thinking about the tool.
User zero (Satvik) is this persona: M1 Air 8 GB at home, Windows laptop at the company.

**P2. The company-laptop worker (v2).** Windows, 8 GB, no GPU, IT blocks downloads and installers.
Types Roman Hindi on WhatsApp all day. Job: "Dictate a message or a ticket the way I would type
it." Needs: zip install, no admin rights beyond Python, CPU speed.

**P3. The Hindi-first creator or ops person (v3).** Cheapest Windows laptop, 4 GB. Comfortable with
Roman Hindi, weak with English spelling. Job: "Say it in Hindi, get it in Roman letters so my
phone-typing friends read it." Needs: the micro profile, forgiving accuracy, zero setup.

**Not for:** native English speakers (Parakeet-only tools serve them already). Devanagari writers
(a different product). Meeting transcription (long-form, a different latency shape).

Prioritisation: P1 first, because user zero is P1 and can measure daily. P2 second, because user
zero also owns that laptop. P3 sets the floor hardware profile and the accuracy bar.

### A5. Experience: journey, states, wireframes

There is no window. The "UI" is a key, the cursor, and one line of terminal output. So the
wireframes are states and text.

**State machine.**
```
IDLE ──key down──▶ RECORDING ──key up──▶ ROUTING (~50 ms) ──▶ TRANSCRIBING ──▶ INSERTING ──▶ IDLE
  ▲                     │ under 0.3 s of audio: drop, back to IDLE                        │
  └──────────────────────────────────────── on error: print one line, keep running ◀──────┘
```

**Terminal output, one line per dictation (the only visible feedback).**
```
[12:03:41] en   lid 48ms  asr 412ms  insert 31ms   "send the deck to rahul by tonight"
[12:03:59] hing lid 51ms  asr 903ms  insert 29ms   "kal subah wali meeting shift kar do please"
```

**First run (mac).**
```
$ uv run dictate.py
models: tiny ✓ parakeet ✓ apex ✓  (2.1 GB, 3.4 s)
permissions: Microphone ✓  Accessibility ✗ → System Settings › Privacy › Accessibility › add Terminal
hold Right Option to talk. ctrl-c to quit.
```

**Feedback that recording is happening: sound, not screen.** The user must know the mic is live
and when the text has landed. v1 does this with two short sounds: one when the key goes down
(recording started), one when the text is inserted (done). macOS plays a system sound file via the
stdlib (`afplay /System/Library/Sounds/Tink.aiff` or `NSSound`); Windows uses the stdlib
`winsound`. No screen space, no window, no extra dependency. The stdout line stays for debugging.

**What a "tray icon" is, and why v1 has none.** A tray icon is the small always-visible icon in
the macOS menu bar (top right) or the Windows system tray (bottom right) that shows an app is
running and opens a menu when clicked. It is not the recording indicator. It costs an app event
loop and one more dependency (`rumps` or `pystray`), and it only says "I am running", which the
terminal already says. It does not block the single-zip rule and needs no Node server, so it can
be added later in a few lines if the owner wants it. The owner's real need (know when capture
starts) is met by the sounds above.

**"Ease" UI.** The owner asked to reuse the UI of a GitHub project called Ease. Web search did
not find a repo by that name; the owner will share the link. The rule for evaluating it: reuse only
if it needs no Node/Electron server, keeps the single zip, and adds no background process. If it is
a Tauri or Electron app, the answer is no for v1 and its design is copied as sounds and, later, an
optional overlay.

**Failure states (what happens, what the user hears and sees, what we decided for v1).**
| Situation | What the app does | What the user hears / sees | v1 decision |
|---|---|---|---|
| Key tapped for under 0.3 s | drops the clip, no model runs | no "done" sound; line: `dropped (0.2s)` | drop silently; a tap is never a dictation |
| Cursor is in a password field | AX insert is refused by macOS; the paste fallback would still paste the text into the field | text appears in the password field | accept in v1; v2 checks for a secure field and refuses with a sound |
| The front app rejects AX insert (some Electron apps, terminals) | falls back to clipboard paste, restores the old clipboard | text appears; line: `insert paste 40ms` | automatic, no user action |
| The front app accepts AX but shows nothing (silent failure) | nothing visible; we cannot detect it from the return code | text missing | found by the acceptance matrix per app; if any app does this, v1 switches to paste for all apps |
| Nothing is focused (desktop) | AX fails, paste goes nowhere | nothing appears; line shows the text | keep the text in the clipboard so the user can paste it themselves |
| Mic permission denied | stream cannot open | exits with: grant Microphone to Terminal in System Settings › Privacy | exit with the exact instruction |
| Accessibility permission denied | hotkey never fires, AX insert fails | exits with: grant Accessibility to Terminal | exit with the exact instruction |
| Model folder missing | cannot start | exits with the full expected path | exit |
| Running under Rosetta | refuses to start | exits with "arm64 only" | exit (ADR-008) |
| Model throws on a clip | catch, log one line, keep running | no "done" sound; line: `error: …` | never crash the session on one clip |
| Two key presses overlap | second press ignored while transcribing | one result | one dictation at a time |

**Two-key layout (fallback if auto routing fails its gate).** Same output; `KEYS` has two entries.

**Insertion methods: all of them, behind one constant, then a feel test.** The owner wants to try
each method and judge by feel before locking one. So `INSERT` is a constant with these values, all
implemented (each is a few lines):
| Value | What it does | Where it comes from |
|---|---|---|
| `ax` | Accessibility API sets the selected text of the focused element | FluidVoice (code read) |
| `paste` | clipboard + Cmd+V (Ctrl+V), restore old clipboard | Handy, VoiceInk, most tools |
| `paste_shift` | clipboard + Cmd+Shift+V (Ctrl+Shift+V) for terminals and "paste without formatting" | terminals, Windows consoles |
| `type` | simulated keystrokes, character by character | pynput; rejected by FluidVoice for IMEs and IDEs |
| `ax_then_paste` | `ax`, and `paste` when `ax` returns an error | FluidVoice and the Wispr Flow clones; our default to start |
Why `ax_then_paste` is the starting default: FluidVoice's authors chose AX because keystroke events
behave unpredictably in terminals and IDEs and break input methods; AX changes nothing in the
clipboard and has no key timing. Wispr Flow needs the Accessibility permission, but that permission
is required for both AX insert and simulated Cmd+V, so it does not tell us which they use. The
owner's feel test (story S5.0) is the deciding data: each method used for one day each in the same
five apps, notes in the journal, then `INSERT` is set.

### A6. Product requirements document

**Problem.** Bilingual Indian users lose their flow because dictation tools lag on Hindi, rewrite
their words, and do not run on locked-down or cheap machines.

**Goals.** G1 sub-second English and near-second Hinglish on an M1 8 GB. G2 exact pass-through.
G3 one key. G4 offline with bundled weights. G5 runs on floor hardware through profiles. G6 a
journey documented well enough to stand as a case study.

**Functional requirements.**
| ID | Requirement | Priority |
|---|---|---|
| FR1 | Hold one global key to record; release to transcribe and insert | must |
| FR2 | Audio captured at 16 kHz mono float32 into memory; no temp files | must |
| FR3 | Mic stream stays open; 500 ms of pre-roll is in each clip | must |
| FR4 | A language router decides English vs Hinglish per clip in ≤ 100 ms | must |
| FR5 | English uses Parakeet v2; Hinglish uses Apex with forced `en`, Roman output | must |
| FR6 | Both models stay resident all session; no load or unload between clips | must |
| FR7 | Text inserted at the cursor of the front app; AX first, paste fallback (mac); paste (win) | must |
| FR8 | The old clipboard is restored after a paste fallback | should |
| FR9 | `MODE` pins `auto` / `en` / `hinglish`; `KEYS` maps keys to modes | must |
| FR10 | Clips under 0.3 s are dropped | must |
| FR11 | One stdout line per dictation with stage timings and the text | must |
| FR12 | Windows build with the same behaviour; engine chosen by measurement | must (v2) |
| FR13 | `PROFILE` selects full / lean / micro model sets | must (v2) |
| FR14 | Opt-in local log of (wav, text) when `LOG_DIR` is set | could (v3) |
| FR15 | Personal dictionary applied at dictation time, learned from corrections | could (v3) |
| FR16 | A start sound on key down and a done sound on insert, from system sounds, stdlib only | must |
| FR17 | `INSERT` constant selects `ax` / `paste` / `paste_shift` / `type` / `ax_then_paste`; all implemented | must |
| FR18 | Every dictation appends one row to a local `stats.jsonl` (timestamp, route, stage ms, words, audio seconds); nothing else is stored | must |
| FR19 | No window, no tray icon, no overlay in v1 | must |

**Non-functional requirements.**
| ID | Requirement |
|---|---|
| NFR1 | Latency targets from A1 on an M1 8 GB |
| NFR2 | Resident RAM < 2.5 GB (full), < 1.6 GB (lean), < 0.8 GB (micro) |
| NFR3 | No network calls at run time, verified with tcpdump |
| NFR4 | Apple-silicon native; refuses to run under Rosetta; Python ≥ 3.12 and < 3.14 |
| NFR5 | Code under 25 KB; one script per OS; one pyproject per OS |
| NFR6 | The zip installs with one command and runs with one command |
| NFR7 | No GUI, tray icon or background daemon beyond the script |

**Constraints.** Apache-2.0 / CC-BY models only. GPL code is read for ideas, never copied.

**Release criteria (v1).** Every must-FR for mac passes its Gherkin scenarios. A1 metrics met on
user zero's Mac. Five days of daily use logged in the journal.

### A7. MVP and increments (every step has a demo)

| Increment | What you can show | Done when |
|---|---|---|
| D0 Foundations | Repo, issues, dev branch, CI running an empty test | pytest green on dev, first PR merged |
| D1 Models ready | bench.py prints latency for 4 clips on 3 models | experiments.md has the tables |
| D2 Hear and slice | Hold key, release, a clip-length line prints (no ASR yet) | ring buffer tests green, live demo |
| D3 Hinglish end to end | Hold key, speak Hinglish, text appears in TextEdit | E3 scenarios pass |
| D4 Router and English | Mixed session routes per clip; line shows `en` / `hing` | LID gate decision recorded |
| D5 Flawless insert | Works in Chrome, VS Code, Terminal, Slack; clipboard restored | insertion matrix all green |
| D6 Zip | Fresh mac account, unzip, two commands, dictation works | README followed by a second person |
| D7 Windows | Same on the company laptop, profile set from its specs | FR12, FR13 scenarios pass |
| D8 Data log | `LOG_DIR` fills with pairs | one week of pairs |
| D9 Dictionary | A corrected name is right the second time | E9 scenarios pass |
| D10 Fine-tune | WER on 50 own clips drops vs Apex | experiments.md row |
| D11 Playbook (last) | A fresh agent, given PLAYBOOK.md + a toy IDEA.md, reproduces the setup | S11.4 dry run passes |

MVP = D0 to D6 (user zero's Mac). v2 = D7. v3 = D8 to D10. D11 closes the project.

### A8. Roadmap (what stays in scope after v1)

| Version | Scope | Why it is on the roadmap |
|---|---|---|
| v1 | One key, two models, auto-route, sounds, insert, zip, stats log. Mac. | make it exist for user zero |
| v2 | Windows build on the company laptop; profiles for CPU-only machines; insertion feel test result locked in | the second machine user zero owns; P2 |
| v3 | **Self-improvement dictionary** (E9): applied at dictation time, learned from the user's own corrections, all local. Opt-in data log (E8). | the accuracy gap in v1 is closed by the dictionary, not by a bigger model. This feature stays in scope in every roadmap revision |
| v3 | Secure-field refusal; optional tray icon or overlay if the owner wants it after the feel test | small polish, only if asked |
| v4 | Fine-tune on the user's own data plus public Hinglish sets (E10). Owner is open to building his own dataset if it comes to that. | last option, after the dictionary; a model that starts somewhere and improves from daily input |
| later | micro profile on 4 GB machines (P3); auto hardware detection; Indic-tokenizer models when they appear | the "cheapest device, best speed" vision |

---

## Part B: Engineering

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

### B3. Architecture decision records

Each ADR has context, decision, trade-offs, consequences. They live in `docs/decisions/ADR-NNN.md`.

**ADR-001 Roman-Hinglish output only, never Devanagari.** Context: the 2.5x penalty is the
Devanagari token count. Decision: Roman only. Trade-off: users who want Devanagari are not served.
Consequence: model choice narrows to Apex and Swift; the penalty is removed by construction.

**ADR-002 Two resident models with a 50 ms language router.** Context: Parakeet is better and 2x
faster on English but English-only; Apex handles everything at whisper speed. Decision: tiny LID in
front, threshold 0.8 biased toward Apex. Trade-off: +75 MB RAM, +50 ms per clip, one more model to
convert; a mis-route of Hinglish to Parakeet gives garbage, hence the bias. Fallback: a two-key map.
Consequence: English gets the best model; Hinglish pays only 50 ms for detection.

**ADR-003 MLX on macOS, not whisper.cpp or WhisperKit.** Context: mlx-whisper is 2x faster than
whisper.cpp Metal; WhisperKit and FluidAudio are faster still but Swift. Decision: MLX in Python.
Trade-off: leaves about 2x on the table vs CoreML and the Neural Engine; 30 s padding. Consequence:
one language, one toolchain; revisit only if the latency gate fails.

**ADR-004 Windows whisper engine chosen by a measured gate; one engine shipped.** Context: CT2
installs cleanly but cannot shorten the encoder window; whisper.cpp can, but GPU builds are from
source. Decision: measure both on a 4-thread CPU proxy, ship one. Trade-off: the proxy is faster
than a real Celeron; stated as a lower bound.

**ADR-005 Insertion: AX set first, concealed-clipboard paste fallback, clipboard restore.**
Context: every serious mac tool does this. Decision: the same. Trade-off: AX can report success
yet insert nothing in some Electron apps; the acceptance matrix catches it and the gate can flip to
paste-only.

**ADR-006 Python plus uv, not Rust.** Context: Rust is the house default for CLIs. Decision:
Python. Reason: MLX, parakeet-mlx, mlx-whisper, onnx-asr and faster-whisper are Python; Rust has no
MLX or Parakeet path; a port would be 10x the code for the same latency. Trade-off: not a single
binary; `uv run` is the one-line stand-in. Consequence: revisit when a Rust MLX binding exists.

**ADR-007 Weights bundled in the zip; no Hugging Face at run time.** Context: the company laptop
blocks HF; the user wants one zip. Decision: convert once on a Mac, ship `models/`. Trade-off: a
3 GB zip; model updates mean a new zip. Consequence: install works offline; PyPI is the one remaining
external dependency, mitigated by optional `wheels/`.

**ADR-008 Apple-silicon native only; no Rosetta ever.** Context: Rosetta ends at macOS 28.
Decision: arm64 deps, startup guard, Python < 3.14 pin (pynput crashes on 3.14 with macOS 26), a
platform marker, a bench assert. Trade-off: Intel Macs unsupported. Consequence: nothing breaks at
macOS 28.

**ADR-009 Hardware profiles (full / lean / micro) as one constant, not auto-detection.** Context:
the cheapest-device vision, and no such device to measure yet. Decision: a constant plus a README
table; auto-detect later if people get it wrong. Trade-off: one manual step on Windows.

**ADR-010 No LLM cleanup, no VAD, no streaming in v1.** Context: pass-through is the product.
Decision: none of it. Trade-off: no punctuation beyond what the model emits (Parakeet emits it;
Apex partly). Consequence: smallest code, honest text.

**ADR-011 Self-learning dictionary is local and correction-driven; no LLM required.** Context: the
user wants words they say often to stop being misspelled, with nothing leaving the machine.
Decision: `dictionary.txt`, `initial_prompt` for whisper, a `difflib` swap for both paths, an AX
read-back diff that promotes words corrected twice. Trade-off: false swaps possible; threshold 0.85
and a common-word stoplist. Consequence: improvement without training, and data for a later
fine-tune.

### B4. Risks and mitigations

| # | Risk | Likelihood | Impact | Mitigation | Gate |
|---|---|---|---|---|---|
| R1 | tiny LID mis-routes Indian-accented English or Hinglish | medium | wrong model, garbage text | threshold biased to Apex; two-key fallback | D4 |
| R2 | 8 GB cannot hold three models with a browser open | low | swapping, latency | q4 Apex; drop tiny when `MODE=hinglish` | D1 |
| R3 | mlx-whisper 30 s pad keeps Hinglish above 1.2 s | medium | misses target | q4; pywhispercpp + CoreML encoder; or accept 1.5 s and say so | D1 |
| R4 | AX set reports success but inserts nothing in Electron apps | medium | silent failure | acceptance matrix; flip to paste-only | D5 |
| R5 | Cheap Windows CPU far slower than the proxy | high | lean/micro too slow | real-box test before any claim; `audio_ctx`; Swift | D7 |
| R6 | Apex English quality below turbo | medium | English via Apex path worse | router sends clear English to Parakeet; test | D1 |
| R7 | pynput breaks on a macOS point release | low | no hotkey | pin versions; CGEventTap fallback noted | ongoing |
| R8 | Company laptop blocks PyPI too | medium | no install | `wheels/` in zip | D7 |
| R9 | Scope creep toward a GUI or LLM app | high | bloat | ADR-010; ponytail review on every PR | every PR |
| R10 | Licence slip (copying GPL code) | low | legal | read for ideas only; Apache and MIT deps | PR review |

---

## Part C: Backlog (epics, stories, Gherkin)

Each story becomes one GitHub issue labelled `story`, linked to its epic issue labelled `epic`.
Each scenario below is copied into the issue and into the matching test name.

### E0. Foundations and process
**S0.1 Repo and branches.**
```gherkin
Scenario: repository exists with protected main and a dev branch
  Given a private GitHub repo "bhavna-ai"
  When I list branches
  Then "main" and "dev" exist
  And main only accepts changes through pull requests
```
**S0.2 Docs tree from this plan.** `docs/PLAN.md` (this file), then `docs/strategy.md`,
`docs/market.md`, `docs/personas.md`, `docs/prd.md`, `docs/mvp.md`, `docs/architecture.md`,
`docs/decisions/ADR-*.md`, `docs/risks.md`, `docs/process.md`, `docs/tests/test-cases.md`,
`docs/research/`, `docs/journal/`, `docs/discussions/`, `docs/success/`, `docs/demos/`,
`docs/ideas.md`.
```gherkin
Scenario: every section of the plan has one home in docs/
  Given docs/PLAN.md
  When I open docs/README.md
  Then every Part A, B, C and D section links to exactly one file
```
**S0.3 CI.**
```gherkin
Scenario: CI runs tests
  When I push a commit to dev
  Then GitHub Actions runs pytest and reports a status on the commit
```
**S0.4 Issues.** Every epic and story exists as an issue with labels, on a board
(Backlog / Doing / Review / Done).

### E1. Model preparation and benchmarks (D1)
**S1.1 convert.sh produces local model folders.**
```gherkin
Scenario: Apex converted to MLX q8 and CT2 int8
  Given a throwaway env with torch and transformers
  When I run tools/convert.sh
  Then models/apex-mlx-q8/ contains weights.npz and config.json
  And models/apex-ct2-int8/ contains model.bin and tokenizer.json
  And the throwaway env is deleted
```
**S1.2 bench.py measures latency and LID.**
```gherkin
Scenario: bench reports per-model latency on four clips
  Given four recorded clips in tests/fixtures/
  When I run tools/bench.py
  Then it prints p50 and p90 for tiny-LID, Parakeet and Apex per clip
  And it writes a table to docs/research/experiments.md
```
**S1.3 Gate decisions recorded.** LID gate, latency gate, Windows engine gate, micro gate. Each is
one row with date, numbers and the choice.

### E2. Audio capture and hotkey (D2)
**S2.1 Ring buffer with pre-roll.**
```gherkin
Scenario: a clip includes 500 ms before the key press
  Given the mic stream has been open for 2 seconds
  When the key is pressed at t=2.0 s and released at t=4.0 s
  Then the clip is 2.5 s long
  And its first 500 ms are audio from before t=2.0 s
```
**S2.2 Short clips are dropped.**
```gherkin
Scenario: a tap under 0.3 s does nothing
  When the key is held for 0.2 s
  Then no transcription runs
  And stdout shows "dropped (0.2s)"
```
**S2.3 Hotkey on macOS.**
```gherkin
Scenario: Right Option is the only trigger
  Given Accessibility is granted to the terminal
  When I hold Right Option in another app
  Then recording starts
  When I hold Left Option
  Then nothing happens
```
**S2.5 Sounds.**
```gherkin
Scenario: start and done sounds
  When the key goes down
  Then a short system sound plays within 50 ms
  When the text has been inserted
  Then a different short system sound plays
Scenario: no sound on a dropped clip
  When the key is held under 0.3 s
  Then the done sound does not play
```
**S2.6 Stats row.**
```gherkin
Scenario: one row per dictation
  When a dictation completes
  Then stats.jsonl gains one line with timestamp, route, lid_ms, asr_ms, insert_ms, words, audio_s
  And no audio or text is stored unless LOG_DIR is set
```
**S2.4 Rosetta guard.**
```gherkin
Scenario: refuses to run translated
  Given the process runs under Rosetta
  When dictate.py starts
  Then it exits with "arm64 only" and status 1
```

### E3. Hinglish end to end on macOS (D3)
**S3.1 Apex transcribes a Hinglish clip to Roman text.**
```gherkin
Scenario: Roman output, no Devanagari
  Given the Hinglish fixture clip
  When Apex transcribes it with language "en"
  Then the text is non-empty
  And it contains no code points in U+0900 to U+097F
```
**S3.2 No fallback decoding.**
```gherkin
Scenario: a single greedy pass
  When Apex transcribes any clip
  Then temperature is 0.0 and no retry thresholds are set
  And the call completes in one decode
```
**S3.3 Text inserted in TextEdit.**
```gherkin
Scenario: live dictation lands at the cursor
  Given TextEdit is frontmost with the cursor in a document
  When I hold the key, say "kal subah meeting shift kar do", and release
  Then the words appear at the cursor within 1.5 s
```

### E4. Router and English path (D4)
**S4.1 LID threshold.**
```gherkin
Scenario: clear English goes to Parakeet
  Given a clip where tiny reports p(en) = 0.93
  Then the route is "en"
Scenario: Hinglish goes to Apex
  Given a clip where tiny reports p(en) = 0.55
  Then the route is "hinglish"
Scenario: boundary
  Given p(en) = 0.80
  Then the route is "en"
```
**S4.2 Both models resident.**
```gherkin
Scenario: no load between clips
  Given ten alternating English and Hinglish clips
  When they are transcribed in sequence
  Then no model load happens after startup
  And the ninth and tenth clips are no slower than the first two
```
**S4.3 MODE and KEYS constants.**
```gherkin
Scenario: a pinned mode skips LID
  Given MODE = "hinglish"
  When a clip is transcribed
  Then tiny is not called and Apex is used
Scenario: two-key layout
  Given KEYS = {alt_r: "en", cmd_r: "hinglish"}
  When Right Cmd is held
  Then the clip is routed to Apex without LID
```

### E5. Flawless insertion on macOS (D5)
**S5.0 All insertion methods behind `INSERT`, then the feel test.**
```gherkin
Scenario: every method is selectable
  Given INSERT is one of ax, paste, paste_shift, type, ax_then_paste
  When text is inserted in TextEdit
  Then the text appears at the cursor for each value
Scenario: feel test recorded
  Given the owner uses each method for one day in TextEdit, Chrome, VS Code, Terminal, Slack
  When the week ends
  Then docs/journal has one entry per method with feel notes and any failures
  And docs/decisions/ADR-005 is updated with the chosen default and the reason
```
**S5.1 AX first.**
```gherkin
Scenario: AX insertion in a native app
  Given TextEdit is frontmost
  When text is inserted
  Then the clipboard is unchanged
  And stdout shows "insert ax"
```
**S5.2 Paste fallback with restore.**
```gherkin
Scenario: the app rejects AX set
  Given an app where AXUIElementSetAttributeValue returns an error
  And the clipboard holds "before"
  When text is inserted
  Then the text appears in the app
  And within 1 s the clipboard holds "before" again
```
**S5.3 Acceptance matrix.** TextEdit, Chrome (Gmail compose), VS Code, Terminal, Slack. Each row:
"inserted at cursor, clipboard restored, no stray characters". Dated results in
`docs/tests/test-cases.md`.

### E6. Packaging (D6)
**S6.1 One-line install and run.**
```gherkin
Scenario: fresh user
  Given a clean macOS user account with uv installed
  When they unzip Bhavna.zip and run "uv run macos/dictate.py"
  Then models load from models/ with no network call
  And dictation works after granting the listed permissions
```
**S6.2 No network at run time.**
```gherkin
Scenario: offline session
  Given tcpdump is capturing for the process
  When I dictate ten times
  Then zero outbound packets are attributed to the process
```

### E7. Windows (D7)
**S7.1 Specs captured.** User zero runs the PowerShell line below; the result goes in
`docs/journal/`.
```powershell
Get-CimInstance Win32_VideoController | Select Name; Get-CimInstance Win32_ComputerSystem | Select TotalPhysicalMemory; Get-CimInstance Win32_Processor | Select Name
```
(Or: Task Manager → Performance → GPU name; Settings → System → About for RAM and CPU.)
**S7.2 Engine per gate.** Same Gherkin as E3 and E4 with the chosen engine; `PROFILE` set.
**S7.3 Paste insertion with restore.** Same as S5.2 with Ctrl+V.
**S7.4 Runs on the company laptop.** Live demo logged.

### E8. Opt-in data log (D8)
```gherkin
Scenario: LOG_DIR set
  Given LOG_DIR points to a folder
  When I dictate
  Then a wav and a txt with the same stem appear there
Scenario: LOG_DIR unset
  Then nothing is written anywhere
```

### E9. Self-learning dictionary (D9)
```gherkin
Scenario: a dictionary word is applied
  Given dictionary.txt contains "Miraya"
  When the model outputs "Miraaya"
  Then the inserted text says "Miraya"
Scenario: learned from a correction
  Given I dictate and the field later reads "Rahul" where we pasted "Rahool", twice
  Then dictionary.txt gains "Rahul"
Scenario: nothing leaves the machine
  Then the helper makes no network call
```

### E10. Fine-tune (D10)
```gherkin
Scenario: measurable gain
  Given 50 held-out own clips
  When the LoRA model is evaluated against Apex
  Then WER is lower and the row is in experiments.md
```

### E11. The repeatable playbook (the last task of the project)
The owner wants this whole way of working, from the first message in this chat to the last
merge, captured as one document he can hand to any coding agent together with one idea file, so
the same setup reproduces for the next idea. This epic runs across the whole project and closes
last.

**S11.1 Process trace, kept from the first message.**
```gherkin
Scenario: every step is logged as it happens
  Given docs/process-trace.md exists from day one
  When any of these happens: owner brief, question asked to the owner, feedback received,
       research round, document created, decision taken, issue created, PR opened, demo shown,
       measurement window closed
  Then one line is appended with: date, step number, actor (owner / agent), what was done,
       which artifact changed, and whether feedback was asked for or volunteered
```
**S11.2 PLAYBOOK.md written from the trace, not from memory.**
```gherkin
Scenario: the playbook is a prompt
  Given docs/process-trace.md is complete to the last merge
  When PLAYBOOK.md is written
  Then it lists the phases in the exact order they happened, with for each phase:
       the inputs, the artifacts produced, the questions the agent must ask the owner and when,
       the options it must offer, how it captures feedback, and the exit check (Definition of Ready)
  And it contains the GitHub setup, branching, TDD loop, demo cadence, measurement windows,
       discussion log, ideas log, success stories, and the Definitions of Ready and Done
  And it contains a section "What we would do differently", built from the trace
  And it is written as instructions to a coding agent, in plain English, under 1,500 words,
       with IDEA.md as its only required input
```
**S11.3 IDEA.md template.**
```gherkin
Scenario: the idea file is enough to start
  Given IDEA.md with: the user quote, who the owner is relative to that user, the problem, the
        non-goals, the machines it must run on, the accuracy bar, and what "done" feels like
  When PLAYBOOK.md and IDEA.md are given to a fresh agent session
  Then the agent produces the docs tree, the issues skeleton and the first questions
       without asking for anything else
```
**S11.4 Dry run.**
```gherkin
Scenario: reproducibility proven on a toy idea
  Given a one-paragraph toy idea
  When a fresh agent runs PLAYBOOK.md with it
  Then the repo it creates has the same docs/ layout, labels, board and first PR as this project
  And the differences are logged as improvements to PLAYBOOK.md
```

---

## Part D: Process (how the work runs)

### D1. Order of operations, fixed
0. Create `docs/process-trace.md` from Appendix B and `docs/discussions/2026-10-07.md` from
   Appendix A. Write the project `CLAUDE.md` with the standing rule from D9 (read the trace first,
   append before done, keep the discussion log, log ideas at once). From here every step appends
   to the trace (S11.1).
1. Copy this file to `docs/PLAN.md`. Create the repo, branches, labels, board (S0.1).
2. Split the plan into `docs/` (S0.2). Commit. First PR.
3. Create every epic and story as a GitHub issue with its Gherkin (S0.4). No code before this.
4. Log every idea so far to `docs/ideas.md` and to the SecondBrain ideas log
   (`~/Desktop/SecondBrain/Ideas/`, via `tools/idea.py`; register the folder as an Obsidian vault
   once with "Open folder as vault").
5. Only then: Phase 0 benchmarks, then increments D1 → D6 in order. Nothing is built in one shot.

### D2. Branching and review
- `main`: protected, release-ready. The owner merges.
- `dev`: integration branch. Pushed to after every green test run; at least daily, usually per story.
- `feat/<issue-number>-<slug>`: one branch per story, from dev.
- PR feat → dev: opened by Claude, self-reviewed with a checklist comment (tests first, Gherkin
  mapped, ponytail review, docs updated), merged by Claude after CI is green.
- PR dev → main: opened by Claude at each increment (D1 … D6) with the demo notes. The owner merges.
- PR template: issue link, what changed, scenarios covered, test output pasted, demo (gif or
  stdout), decisions made (ADR link), ideas noted.
- Commits: Conventional Commits, English, short. Co-author line as required.

### D3. Test-driven development, strictly
For every story:
1. Write the failing test first, named after the scenario (`test_s2_1_clip_includes_preroll`).
2. Run it. See it fail. Paste the failure in the PR.
3. Write the least code that passes.
4. Refactor with ponytail eyes. Run again.
Rules. Deterministic logic (ring buffer slicing, threshold routing, difflib swap, constants, the
Rosetta guard) gets unit tests with no model loaded. Model paths get smoke tests on the four fixture
clips, marked `slow`, run before every dev → main PR. Insertion is a manual acceptance matrix (no
reliable automation across apps), recorded with dates in `docs/tests/test-cases.md`. Latency
targets are bench rows, not unit asserts. Every test is listed in `docs/tests/test-cases.md` with
its story and scenario id. The `tdd` skill is used for each story.

### D4. Demos and the journey log
- Each increment ends with `docs/demos/D<n>.md`: what you can see, how to run it, the stdout or a
  short recording, what was learned.
- `docs/journal/YYYY-MM-DD.md`: one entry per working session: what was decided, what surprised,
  what was dropped, what was measured. This is the case-study narrative.
- `docs/decisions/ADR-NNN.md`: every decision that changes architecture or scope, added in the PR
  that implements it.
- `docs/ideas.md`: every idea from the owner or Claude, dated, one line, with status (open / taken /
  dropped). Mirrored to the SecondBrain ideas log.
- `docs/research/`: findings with tiers and confidence; `experiments.md` with hypothesis, design,
  result, decision. Rows are never deleted.

### D4b. Discussion log (the unfiltered product thinking)
`docs/discussions/YYYY-MM-DD.md`: one file per conversation between the owner and Claude. Bullet
points, not transcripts: what the owner pointed out, what he pushed back on, what he put emphasis
on, what he asked to be explained, and what was decided or left open because of it. The first
entry is the appendix at the end of this plan. This is where the "why" behind each ADR can be
traced to a sentence the owner said.

### D5. Definition of ready (a story may start only when all are true)
This is the validation step for the planning itself. If a story fails it, the plan is wrong, not
the story.
1. The story is a GitHub issue linked to its epic, with Gherkin scenarios copied in.
2. Every scenario is testable: unit test, slow fixture test, or a named row in the acceptance matrix.
3. The persona and the FR it serves are named in the issue.
4. Dependencies (model folders, permissions, fixtures, the owner's input) are listed and available.
5. The ponytail check is written in the issue: what is deliberately not being built.
6. The owner has seen the issue (he reviews the board before each increment starts).
If any item is missing, the story goes back to Backlog and the plan or the issue is fixed first.

### D6. Definition of done (story)
Tests written first and green. Scenarios mapped to tests or to a matrix row. Docs updated in the
same PR. Ponytail review: nothing speculative added. Issue closed by the PR. Journal entry written.

### D7. Definition of done (increment)
All its stories done. `docs/demos/D<n>.md` written. dev → main PR opened with the demo. Metrics rows
updated. The owner has seen the demo.

### D8. After done: success metrics and success stories
Done is not the end. Each increment is followed by a measurement window and a story.
- **Measurement window.** One week of daily use after D3, D5, D6, D7 and D9. The success metrics
  table (A1) is filled from `stats.jsonl` and the journal. ActivityWatch supplies time-in-app for
  other tools. Rows that cannot be captured yet are marked "not captured" with what would be
  needed, never left blank.
- **Success story.** `docs/success/<date>-<who>.md`: who used it (user zero first), on what
  machine, for what work, what changed in their day, with the numbers. Written in the user's voice,
  like the quote at the top of this plan. These stories are the proof for the case study, and later
  the proof for other users.
- **Is the tool improving itself?** From v3, the dictionary helper logs every swap and every learned
  word. The weekly check: corrections per 100 words should fall, dictionary hits should rise. If the
  trend is flat for four weeks, the dictionary design is wrong and ADR-011 is revisited.
- **Review cadence.** At the end of each measurement window, one journal entry: what the numbers
  say, what the owner felt, what the next increment should change.

### D9. Process trace and the playbook
- `docs/process-trace.md` is appended on every step (S11.1). It starts with Appendix B below,
  which reconstructs the steps already taken in this chat.
- **Standing rule for every future chat on this project:** the first action of a session is to
  read the trace; the last action before any "done" is to append the session's steps to it. Every
  owner message that changes direction, every question asked, every document created, every PR,
  every demo, every measurement window: one row each, same columns, numbered on from the last row.
  This holds until the playbook is written and after it, so the process can be retraced at any
  time. The rule is written into the project `CLAUDE.md` at repo creation so no session can miss it.
- The trace marks the three kinds of owner contact: **asked** (the agent stopped and asked, with
  options), **volunteered** (the owner sent input mid-work), **reviewed** (the owner read a
  document and gave feedback). The playbook turns the first kind into fixed checkpoints and the
  second kind into "expect this; keep a discussion log".
- `PLAYBOOK.md` is the final deliverable of the project (S11.2) and lives at the repo root next to
  `IDEA.md` (S11.3). It is the prompt for the next project.

### D10. Tooling
- `gh` CLI for repo, issues, labels, PRs, branch protection. Verified logged in today as
  satvik-jain-iitd.
- GitHub issues are the task tracker for this project. Beads holds only `bd remember` pointers to
  the docs so other sessions find them (one tracker, not two).
- CI: GitHub Actions on a macOS runner for unit tests (no models). `slow` tests run locally.

---

## Verification of this plan at execution time
- Part A docs exist and read cleanly at a Grade-5 level.
- Every story is a GitHub issue with its Gherkin and label.
- The first dev → main PR contains docs only and is merged by the owner.
- The D1 experiments table has real numbers from user zero's Mac before any claim about speed.
- Live demo of D3 on that Mac: hold the key, speak Hinglish, text appears in TextEdit.

## Skipped on purpose
Devanagari mode; GUI; tray icon; VAD; streaming; LLM cleanup; auto hardware detection; Rust port;
cloud anything. Each is one line in `docs/ideas.md` with status "dropped for v1" and the reason.

---

## Appendix B: process trace of this chat so far (first rows of `docs/process-trace.md`)

| # | Actor | Step | Artifact | Owner contact |
|---|---|---|---|---|
| 1 | owner | Sent the brief: problem, intent, platforms, Ponytail standard, research questions, deliverables | chat | volunteered |
| 2 | agent | Inspected the machine (chip, RAM, Python, uv, ffmpeg); project folder empty | none | none |
| 3 | agent | Loaded the house web-research rules before any search | none | none |
| 4 | agent | Research round 1: models (English, Hinglish), engines (mac, win), hotkey/paste, token-cost root cause | notes | none |
| 5 | agent | Verified primary sources: model config.json, library source for API shapes, benchmark repos | notes | none |
| 6 | agent | Asked 4 questions with options: Windows GPU, Hindi script, hotkey style, weights hosting | question | asked |
| 7 | owner | Answered; pushed back on two modes (wants auto, instant); rejected HF hosting, wants one zip; asked what the risk is | chat | reviewed |
| 8 | agent | Research round 2: routing options, LID, datasets, fine-tune cost; wrote plan v1 | plan | none |
| 9 | owner | Mid-work: research all insertion methods from popular repos; core experience must be flawless | chat | volunteered |
| 10 | agent | Research round 3: FluidVoice source, Wispr clones, Handy; pre-roll and warm-up tricks | plan | none |
| 11 | owner | Mid-work: Apple Rosetta article, factor it in | chat | volunteered |
| 12 | agent | Read the article; verified arm64 on the machine; added ADR-008 | plan | none |
| 13 | owner | Review: cheapest Mac and cheapest CPU-only Windows must work | chat | reviewed |
| 14 | agent | Research round 4: CPU numbers, audio_ctx, small Hinglish models; profiles | plan | none |
| 15 | owner | Review: order (his Mac first, company laptop next), accuracy bar, self-learning dictionary | chat | reviewed |
| 16 | agent | Added order, GPU-check instructions, dictionary design | plan | none |
| 17 | owner | Review: write the complete plan with all inputs | chat | reviewed |
| 18 | agent | Rewrote the plan as one document | plan | none |
| 19 | owner | Review: make it a case study: strategy, PRD, MVP, epics, Gherkin, research, personas, wireframes, GitHub process, TDD, demos | chat | reviewed |
| 20 | agent | Rewrote as Parts A to D; checked gh login | plan | none |
| 21 | owner | Obsidian "Ideas vault does not exist" | chat | volunteered |
| 22 | agent | Diagnosed (folder exists, not registered); gave the fix | chat | none |
| 23 | owner | Review: start from the user's quote; owner is one of the users; store as a markdown file | chat | reviewed |
| 24 | agent | Rewrote with the user-first framing | plan | none |
| 25 | owner | Review: DoR, DoD, success metrics and stories, ActivityWatch, tray icon definition, sounds, Ease UI, insertion feel test, accuracy 80 to 85%, clearer failure states, discussion log | chat | reviewed |
| 26 | agent | Added all of it plus the owner input log | plan | none |
| 27 | owner | Review: make the process repeatable; capture every step; produce a playbook prompt plus an idea file | chat | reviewed |
| 28 | agent | Added E11, D9, this trace | plan | none |
| 29 | owner | Review: the trace must keep expanding across all future chats; finalise and execute | chat | reviewed |
| 30 | agent | Added the standing rule (D9) and the project CLAUDE.md hook; plan finalised | plan | none |

**What we would do differently next time (first entries for the playbook).**
- Ask at step 6, not step 19, how the owner wants the plan shaped (quick plan vs case study) and
  which process (GitHub issues, TDD, demos) he expects. One extra question would have saved four
  rewrites.
- Define every piece of jargon the first time it appears (tray icon, AX, LID). The owner should
  never have to ask "what is that".
- Offer options for anything the owner will judge by feel (insertion method, feedback sound vs
  overlay) instead of deciding from research alone. Research sets the first order; the owner
  decides after trying.
- Start the discussion log and the process trace in the first turn, not at the end.
- Log every idea the moment it is said (the house rule), even in plan mode, by queuing it for the
  first execution step.

## Appendix A: owner input log, 2026-10-07 (first entry of `docs/discussions/`)

What the owner said, pointed out, pushed back on, or put emphasis on, in order. Bullets, his
meaning kept, not his exact words.

- Wants a pure pass-through engine. No AI filters, no cleanup, no LLM formatting, no bloat.
  Existing tools (FluidVoice, Musely, Superwhisper) fail on Hindi speed (about 30% or worse) and
  on bloat.
- Two platforms in one repo: his M1 8 GB Mac and Windows via terminal. Single-file entry per OS.
  Tiny zip apart from weights.
- Pushed back hard on "one model": he does not mind two models, but switching must be instant, both
  loaded, never unloaded. If auto-switch is not feasible, two keys (Option = English, Cmd = Hindi
  plus English), or one key with a default mode in settings.
- Romanized Hindi only. No Devanagari.
- Open to fine-tuning. Wants to know where data comes from and how AI can help. But: first make it
  exist, then improve. Asked for deeper research on how close we can get to the final vision.
- Asked for all insertion methods to be researched from popular repos (FluidVoice and others), and
  named the push-to-talk and insertion experience as the core that must be flawless and blazing
  fast. Said "Wispr Flow is doing something like this, see what they do".
- Sent Apple's Rosetta article and insisted it be factored in for the future.
- Expanded the target: cheapest MacBooks and cheapest CPU-only Windows machines must work equally
  well. Then clarified the order: his Mac first, then the company laptop (he will check its GPU
  and RAM; asked how to check), and the cheapest-device vision as the long-term goal.
- Accuracy: "LLMs understand even with mistakes". 80 to 85% is a fine start. He differs from the
  Wispr Flow CTO on wanting everything correct. The dictionary closes the gap.
- Self-learning dictionary must be in the future roadmap: a local background helper that sees which
  spellings were corrected and adds frequent words. No data leaves the machine.
- Asked for the plan to be a case study: product strategy, PRD, MVP, epics, stories with Gherkin,
  competitor and market research, industry research, personas, wireframes, decisions, trade-offs,
  risks. GitHub issues, dev branch, PRs reviewed then merged by him, TDD with documented test
  cases, frequent pushes, something demoable at every step, the journey documented, his ideas
  noted.
- Asked that the plan start by quoting the general user, then say he is one of those users.
- Flagged an Obsidian error "Ideas vault does not exist". Cause: the Ideas folder exists on disk
  but is not registered in Obsidian. Fix: Open folder as vault.
- Asked for Definition of Ready as a planning validation step, Definition of Done, and after it
  success metrics and customer success stories. He has ActivityWatch and wants words spoken, time
  used vs FluidVoice, and time saved tracked, plus a way to see if the tool is improving itself.
- Did not know what a tray icon is; asked for a definition and the real reason for leaving it out.
  Decided: no GUI in v1; feedback by a short sound at start (like the system recording sound) and
  at done. Asked to look at the UI of a repo called "Ease" and reuse it if that does not need a
  node server or break the single zip.
- Corrected the daily-use metric: he uses FluidVoice, not Superwhisper; say "no alternative app".
  Write every metric down even if it cannot be captured yet.
- Asked why AX insertion was chosen. Wants all paste methods implemented and to judge by feel
  before deciding; research can set the first order only.
- Could not follow the failure-states table; asked for clearer behaviour per state.
- Wants an unfiltered discussion log kept, with bullets of what he highlighted and emphasised, to
  show the product thinking.

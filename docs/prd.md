# Product requirements document

<!-- Source: docs/PLAN.md. Edit there, then re-split. -->

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

# Process trace

One row per step, from the first message of the project. Owner contact: asked / volunteered / reviewed / none.
Rule: read this first in every session, append before saying done.

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
| 31 | agent | Plan approved. Logged 7 ideas (ID020 to ID026) to the SecondBrain ideas log; opened the Ideas folder as an Obsidian vault | SecondBrain | none |
| 32 | agent | Created repo skeleton, CLAUDE.md with the standing rules, .gitignore, ideas.md, process-trace.md, discussions/2026-10-07.md; private repo satvik-jain-iitd/bhavna-ai; branches main and dev | repo | none |
| 33 | agent | Split the plan into the docs tree, 11 ADRs, research tables (25 rows, tiers), experiments H1 to H8, test-cases.md, journal, README, CI, placeholder test; PR #1 feat -> dev, CI green, merged | docs, PR #1 | none |
| 34 | agent | Labels; 12 epic and 33 story issues with Gherkin, DoR, DoD; branch protection refused (private repo, free plan); project board needs owner auth scope | issues | none |
| 35 | agent | Demo D0 written; dev -> main PR opened for the owner to merge | PR #2 | asked (merge) |
| 36 | agent | Models converted (two fixes: numba, weights file name); fixtures made (4 TTS + 8 Apex clips); bench run | models/, tests/fixtures, experiments.md | none |
| 37 | agent | E2 audio/hotkey/sounds/stats with TDD (red then green), PR #48 merged; E4 router tests PR #49 merged | dictate.py, tests | none |
| 38 | agent | H1 pass (auto routing ships), H2 pass (Apex English word-perfect), H4 pass (Parakeet 0.45 s), H3 fail (Apex 5 s flat: 30 s encoder pad); H3b: window cut 15 s / 10 s gives 2.8 / 2.0 s, fp16 no gain, whisper.cpp 15 s 1.9 s | experiments.md | none |
| 39 | owner | Mid-work: the laptop was swapping hard (5.6 of 6 GB); asked for RAM consideration | chat | volunteered |
| 40 | agent | Stopped the bench; memory back to 50% free; RAM rules added to process; asked the owner when to run the last window test and whether the Mac profile should drop Parakeet to save 1.2 GB | process.md | asked |
| 41 | owner | Decided: bench runs only when he says; Mac default profile = lean (Apex only) | chat | asked, answered |
| 42 | agent | ADR-012 lean profile + dynamic 5 s-step encoder window, implemented with tests (red then green), PR #51 merged; D1 PR #50 merged after a docs-only conflict; README, demo D1, journal PR #52 merged | dictate.py, docs | none |
| 43 | agent | dev -> main PR #47 now carries D0 and D1; owner to merge. Next: D3 live test needs the owner at the keyboard, permissions, and a model load he approves | PR #47 | asked (merge, go-ahead) |
| 44 | owner | Asked how to test; ran the engine on his Mac; first 5 real dictations; reported: works, small accuracy slips, fast on short, long untested, paste fails in Claude Code | stats.jsonl | reviewed |
| 45 | agent | Read stats (0.86 s for 2.8 s, 5.1 s for 24 s); confirmed R4 (AX silent failure in terminals); added the settable check and the insert method in stats, tests green, PR | dictate.py, experiments.md | none |
| 46 | owner | Asked that the bug be logged first with full details | chat | volunteered |
| 47 | agent | Logged #54 (AX silent failure in terminals) and #55 (11 s clip to one word); added rule D12 "log the bug before the fix"; linked PR #53 | issues, process.md | none |
| 48 | owner | Explained #55: FluidVoice was running with Option+Space; the Option press also fired our hotkey. Not a bug | chat | volunteered |
| 49 | agent | Closed #55 as not-a-bug with the explanation; README note on running one dictation tool at a time | issue, README | none |
| 50 | owner | Verified #54 working in Claude Code after the fix (and with FluidVoice closed) | chat | reviewed |
| 51 | agent | Posted the verification comment with stats evidence (`insert: paste` rows), closed #54, regression row set to working | issue, test-cases.md | none |
| 52 | owner | Tuned the feedback sound volume live: 3x too low, 5x ok, 10x too loud, settled on 3x; asked for a `bhavna` launcher | chat | volunteered |
| 53 | agent | Demo D3 written from the owner's live session; tools/zip.sh (mac zip with the lean model) for D6 | demos/D3.md, tools/zip.sh | none |
| 54 | owner | Reported: long sentences cut part way; guessed the recording did not stop after key release | chat | volunteered |
| 55 | agent | Stats showed 46 s and 49.7 s clips with half the words: the 30 s window trimmed the tail. Logged #56 (sub-issue of S3.1) before fixing; fix = split at quiet points + 300 ms post-roll; tests red then green; PR | issue #56, dictate.py | none |
| 56 | owner | "Fix karo, lamba audio aana chahiye" | chat | volunteered |
| 57 | agent | Verified #56 on a 33 s synthetic clip (split 28.2 + 5.1 s, tail present), closed with evidence; one model loaded, memory 57% free | issue #56 | none |
| 58 | owner | Liked the self-run spot test with a synthesised Hindi clip; asked to make it part of the process | chat | volunteered |
| 59 | agent | Added rule D13 "spot test before handing back" (synthesise with `say`, run the real path, paste the result) | process.md | none |
| 60 | owner | Asked why long transcription is slow; guessed "all at once after release" | chat | volunteered |
| 61 | agent | Explained the cost (encoder ∝ window, decoder ∝ words, nothing starts before release); proposed streaming chunks at pauses while talking | chat | asked (go / no-go) |
| 62 | owner | Asked for a proper solution with every scenario mapped; issue rule (story / bug sub-issue / test sub-issue); log on by default for the dictionary dataset; then "start in plan mode"; then epic-level SIT test sub-issues; then deep research on the leaders; then "measure first, numbers not gut, log it all" | chat | reviewed, asked |
| 63 | agent | D14 rule; story #58 with 16-row scenario map and test sub-issues #59 to #69, #85; story #70 (#71, #72); 12 epic SIT sub-issues; S4.4 #86; research rows 26 to 31; measurement section (release_to_text identity, targets, report tool, decision table) in the approved plan | issues, process.md, stt_models.md | none |
| 64 | agent | S3.4 + S8.1 built with TDD (14 tests), spot test found #88 and #89, both logged first, fixed, verified; PR #87; H9 recorded | dictate.py, issues, experiments.md | none |
| 65 | owner | Offered a live "podcast": agent asks, owner dictates answers in Hinglish; "uspe kaam chalu hai na?" | chat | volunteered |
| 66 | owner | Proposed the read-aloud accuracy test (reference passage on screen, owner reads, diff) | chat | volunteered |
| 67 | agent | S9.0 story, tools/wer.py, passage 001, accuracy.md (PR #93); first live read-aloud: WER 35% strict, tail missing | accuracy.md | none |
| 68 | agent | Found the real-mic bug from the log (speech_s 1.3 of 40.7 s, one chunk, tail trimmed); logged it as a sub-issue of #58 before fixing | issue | none |
| 69 | owner | Read passage 004 live on the fixed engine; reported a new bug: inserted text came out in English | chat | reviewed |
| 70 | agent | #94 verified and closed (8 pause cuts, full text); logged the short-final-chunk loop bug and the English-insert bug (needs info); accuracy row 004 | issues, accuracy.md | asked (app + sample) |
| 71 | owner | Asked to learn terminal-without-mouse commands and use that passage as the test | chat | volunteered |
| 72 | agent | Passage 005 read live: full text, no English, no loop (#96/#97 working on this run), but 0 pause cuts / 5 forced: the noise floor stuck low when the pre-roll was very quiet; next fix is a floor that follows the gaps between words | accuracy.md | none |
| 73 | agent | #99 logged from the 19:04 recording (floor ≈ speech, 73% energy under 1 kHz, likely AirPods); detector moved to the 300 to 3400 Hz band with a pre-roll floor; tail never trimmed; all three owner recordings pass; asked the owner whether AirPods were in | dictate.py, tests, issue #99 | asked |
| 74 | owner | Asked for a self-learning dictionary from the dictation logs; wants the logs used, then the audio dropped | chat | volunteered |
| 75 | agent | Read all 166 logged texts; 99 heard-to-correct pairs saved to dictionary.tsv (local, git-excluded: holds personal and client names); design for apply + prompt hint + learn loop given to owner | dictionary.tsv | asked |
| 76 | agent | #103: dictionary applied before insert (load_dictionary, apply_dictionary), raw text kept in log, dict_swaps in stats; ADR-014; 6 unit tests green; 3 owner wavs restored from Trash for test_bug_94 | dictate.py, tests, ADR-014 | none |

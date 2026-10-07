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

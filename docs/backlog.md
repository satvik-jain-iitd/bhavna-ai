# Backlog: epics, stories, Gherkin

<!-- Source: docs/PLAN.md. Edit there, then re-split. -->

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

# Process: how the work runs

<!-- Source: docs/PLAN.md. Edit there, then re-split. -->

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

### D11. RAM rules for the owner's machine (added 2026-10-07 after the swap incident)
- The laptop is the owner's daily machine. Before any model load or conversion: read
  `sysctl vm.swapusage`; above 2 GB used, do not run, say so.
- Benchmarks load one model per process (`ONLY=`), never all at once unless the owner asks.
- No torch or transformers environment again; conversions are done, outputs are in `models/`.
- Heavy runs (more than one model, more than two minutes) are asked for, not started.
- `uv cache prune` after a conversion session.

### D12. Bugs (added 2026-10-07 after the first live bug)
Any defect found in use or in test is logged as a GitHub issue with label `bug` before the fix is
written: summary, environment, steps, expected, actual, evidence, root cause, fix, test gap, status.
The fixing PR says `Fixes #n`. The bug and the fix also get a row in experiments.md if a hypothesis
was wrong, and a line in the journal.

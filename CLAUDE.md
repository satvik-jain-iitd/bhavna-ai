# Bhavna.ai project rules

Read first: `docs/PLAN.md` (the plan and case study) and `docs/process-trace.md`.

Standing rules, every session:
1. First action: read `docs/process-trace.md`. Last action before "done": append this session's steps to it (one row each: date, step, actor, what, artifact, owner contact asked / volunteered / reviewed).
2. Every owner message that changes direction gets bullets in `docs/discussions/YYYY-MM-DD.md`.
3. Every idea the owner states is logged at once with `~/Desktop/SecondBrain/tools/idea.py` and one line in `docs/ideas.md`.
4. Work only from GitHub issues. Branch `feat/<issue>-<slug>` from `dev`. PR feat -> dev (self-review checklist, CI green). PR dev -> main at each demo increment; the owner merges main.
5. TDD: failing test first, named after the Gherkin scenario, failure pasted in the PR. Tests listed in `docs/tests/test-cases.md`.
6. Ponytail: only the code the story needs. No GUI, tray, VAD, streaming, LLM cleanup (ADR-010).
7. Definition of Ready before a story starts; Definition of Done before it closes (docs/PLAN.md Part D).
8. Decisions that change architecture or scope get `docs/decisions/ADR-NNN.md` in the same PR.
9. Apple-silicon native only. Never Rosetta. Python >= 3.12 < 3.14 (ADR-008).
10. Models live in `models/` (gitignored, shipped in the zip). Never download at run time (ADR-007).

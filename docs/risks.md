# Risks and mitigations

<!-- Source: docs/PLAN.md. Edit there, then re-split. -->

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

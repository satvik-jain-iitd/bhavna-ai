# MVP and increments

<!-- Source: docs/PLAN.md. Edit there, then re-split. -->

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

# Bhavna.ai

Local Hinglish dictation. One key. Instant. No bloat.

Hold one key, speak Hindi, English or both mixed, release. Your exact words land at the cursor as
Roman text. Nothing leaves the machine. No window, no tray icon: a short sound when recording
starts and another when the text is in.

Plan and case study: `docs/PLAN.md`. Docs index: `docs/README.md`.

## macOS (Apple silicon, macOS 13.5+, no Rosetta)

Install `uv` once: `curl -LsSf https://astral.sh/uv/install.sh | sh`

Run:
```
uv run --python 3.12 --project macos macos/dictate.py
```
First run installs the Python packages (about 1 minute). Models load from `models/` (shipped in the
zip; never downloaded).

Permissions, once, in System Settings › Privacy & Security, for the app that runs the script
(Terminal, iTerm, VS Code):
- Microphone
- Accessibility (hotkey and text insertion)
- Input Monitoring (macOS 26 asks for this too)

Then hold **Right Option**, speak, release.

Constants at the top of `macos/dictate.py`:
| Constant | Default | Meaning |
|---|---|---|
| `PROFILE` | `lean` | `lean` = Apex only (~0.9 GB RAM, English and Hinglish). `full` = tiny + Parakeet + Apex (~2.3 GB, faster English, auto language routing) |
| `KEYS` | `{"alt_r": MODE}` | key → mode. Two keys: `{"alt_r": "en", "cmd_r": "hinglish"}` (full profile) |
| `MODE` | `auto` | `auto` / `en` / `hinglish` (full profile only) |
| `INSERT` | `ax_then_paste` | `ax` / `paste` / `paste_shift` / `type` / `ax_then_paste` |
| `WINDOW_STEP_S` | `5` | encoder window step in seconds (ADR-012) |
| `LOG_DIR` (env) | unset | when set, saves `(wav, txt)` per dictation for the dictionary and fine-tune phases |

Each dictation prints one line with timings and appends one row to `stats.jsonl` (no text stored).

## Windows

Arrives with increment D7, after the company laptop's specs are known. To check them, in PowerShell:
```powershell
Get-CimInstance Win32_VideoController | Select Name; Get-CimInstance Win32_ComputerSystem | Select TotalPhysicalMemory; Get-CimInstance Win32_Processor | Select Name
```

## Models

`models/` holds converted weights (gitignored, inside the zip). To rebuild them on a Mac:
`tools/convert.sh` (one-time, needs internet and ~6 GB free, deletes its own environment).

| Folder | Use | Size |
|---|---|---|
| `apex-mlx-q8` | Hinglish and English, mac | 837 MB |
| `tiny-mlx` | language ID, mac (full profile) | 38 MB |
| `parakeet-v2-mlx` | English, mac (full profile) | 1.2 GB |
| `apex-ct2-int8`, `tiny-ct2`, `parakeet-v2-onnx`, `ggml/` | Windows (engine chosen by measurement) | see D7 |

Licences: models Apache 2.0 (Oriserve Apex, OpenAI whisper-tiny) and CC-BY-4.0 (NVIDIA Parakeet).

## Status

D0 and D1 done. Live test on the owner's Mac (D3) next. See `docs/mvp.md` and `docs/demos/`.

# Experience: states, feedback, failure states, insertion methods

<!-- Source: docs/PLAN.md. Edit there, then re-split. -->

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

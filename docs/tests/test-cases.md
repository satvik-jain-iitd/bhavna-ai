# Test cases

Every test maps to a story and a Gherkin scenario. Manual rows carry a date and a result.

| Test | Story | Scenario | Kind | Status |
|---|---|---|---|---|
| tests/test_placeholder.py::test_ci_runs | S0.3 | CI runs tests | unit | green |
| tests/test_s2_audio.py::test_s2_1_clip_includes_preroll | S2.1 | a clip includes 500 ms before the key press | unit | green |
| tests/test_s2_audio.py::test_s2_1_preroll_does_not_grow_without_bound | S2.1 | pre-roll stays bounded | unit | green |
| tests/test_s2_audio.py::test_s2_2_short_clip_is_dropped | S2.2 | a tap under 0.3 s does nothing | unit | green |
| tests/test_s2_audio.py::test_s2_6_stats_row_written | S2.6 | one row per dictation | unit | green |
| tests/test_s2_audio.py::test_s2_4_rosetta_guard | S2.4 | refuses to run translated | unit | green |
| manual | S2.3 | Right Option is the only trigger | matrix | pending live test |
| manual | S2.5 | start and done sounds | matrix | pending live test |

## Insertion acceptance matrix (S5.3, manual, owner's feel test S5.0)

Rows: app. Columns: INSERT value. Cell: `ok` (inserted at cursor, clipboard restored, no stray characters) / `fail:<what>` / `silent` (AX success code, nothing inserted). Date each fill.

| App | ax | paste | paste_shift | type | ax_then_paste | Feel notes |
|---|---|---|---|---|---|---|
| TextEdit | pending | pending | pending | pending | pending | |
| Chrome (Gmail compose) | pending | pending | pending | pending | pending | |
| VS Code | pending | pending | pending | pending | pending | |
| Terminal | n/a (not settable) | pending | pending | pending | ok 2026-10-07 (falls back to paste) | Claude Code prompt, 4 dictations |
| Slack | pending | pending | pending | pending | pending | |
| tests/test_s4_router.py::test_s4_1_clear_english_goes_to_parakeet | S4.1 | clear English goes to Parakeet | unit | green |
| tests/test_s4_router.py::test_s4_1_hinglish_goes_to_apex | S4.1 | Hinglish goes to Apex | unit | green |
| tests/test_s4_router.py::test_s4_1_boundary_is_english | S4.1 | boundary p(en)=0.80 | unit | green |
| tests/test_s4_router.py::test_s4_1_unknown_language_goes_to_apex | S4.1 | fail-safe to Apex | unit | green |
| tests/test_s4_router.py::test_s4_3_pinned_mode_skips_lid | S4.3 | a pinned mode skips LID | unit | green |
| tests/test_s4_router.py::test_s4_3_two_key_layout_is_one_dict_entry | S4.3 | two-key layout | unit | green |
| tools/bench.py + experiments.md H1 | S4.1 | LID gate on real clips | bench | see experiments.md |
| tests/test_s3_window_profile.py::test_window_rounds_up_to_5s_steps_with_floor_and_cap | ADR-012 | encoder window = clip rounded up to 5 s, min 5, max 30 | unit | green |
| tests/test_s3_window_profile.py::test_lean_profile_loads_apex_only | ADR-012 | lean loads Apex only, full loads three | unit | green |
| tests/test_s3_window_profile.py::test_lean_profile_routes_everything_to_apex | ADR-012 | lean never routes to Parakeet | unit | green |

## Regression (one row per closed bug, re-checked at every increment demo)

| Bug | Check | Last result |
|---|---|---|
| #54 AX silent failure in terminals | matrix row Terminal × ax_then_paste must show `insert paste` and text present | working, owner, 2026-10-07 16:15 (stats rows show `insert: paste`) |
| #55 11 s clip to one word | closed, not a bug: hotkey collision with FluidVoice (Option+Space) running at the same time | n/a |
| tests/test_bug_long_clips.py::test_short_clip_is_one_piece | #56 | clips under 30 s untouched | unit | green |
| tests/test_bug_long_clips.py::test_long_clip_splits_at_the_quiet_point_and_keeps_everything | #56 | 70 s clip → ≤30 s pieces, cut in the pause, nothing lost | unit | green |
| tests/test_bug_long_clips.py::test_postroll_constant | #56 | 300 ms post-roll after key release | unit | green |
| #56 long dictation cut at 30 s | Regression: a 45 s dictation keeps its tail (≈4 w/s) | pending owner verification |

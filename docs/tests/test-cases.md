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
| #56 long dictation cut at 30 s | Regression: a 45 s dictation keeps its tail (≈4 w/s) | working, agent, 2026-10-07 16:40 on a 33 s synthetic clip (28.2 + 5.1 s pieces, 99 words, tail present); owner live check pending |

## SIT (system integration, one per epic, GitHub sub-issues of the epic)

| Epic | Check | Last result |
|---|---|---|
| E0 | fresh clone → pytest green; docs links resolve | pending |
| E1 | bench.py on 12 fixtures ends ok | green 2026-10-07 (first run) |
| E2 | sounds + stats row on a 2 s hold; tap → dropped | pending |
| E3 | 45 s Hinglish into TextEdit, complete, release-to-text ≤ 1.5 s | pending (S3.4) |
| E4 | full profile alternating clips route correctly, no reload | pending |
| E5 | insertion matrix all ok | pending |
| E6 | fresh account install + tcpdump zero | pending |
| E7 | company laptop E3 flow | pending |
| E8 | 5 dictations → 15 log files matching stats | pending |
| E9 | corrected word right next time | pending |
| E10 | WER lower on 50 own clips | pending |
| E11 | fresh agent reproduces skeleton | pending |
| tests/test_s3_4_chunker.py (T1 to T9) | S3.4 #59 to #67 | chunker, worker, route-once scenarios | unit | green |
| tests/test_s8_1_log.py (T1, T2) | S8.1 #71, #72 | three files per dictation; empty LOG_DIR writes nothing | unit | green |
| tests/test_s3_4_report.py | S3.4 #85 | report buckets, percentiles, before/after split | unit | green |
| tests/test_bugs_window_repeat.py | #88 #89 | window keeps 1 s slack; repeat guard collapses loops, keeps honest repeats | unit | green |
| #88 tight window → nan | Regression: spot clip first chunk is not `nan` | pending re-run |
| #89 repetition loop | Regression: spot clip has each sentence once, `repeats` 0 | pending re-run |
| #88 tight window → nan | Regression: spot clip first chunk is not `nan` | working, agent, 2026-10-07 |
| #89 repetition loop | Regression: spot clip has each sentence once | working, agent, 2026-10-07 (guard caught 2) |
| tests/test_s9_0_wer.py | S9.0 T1 | WER and gap list | unit | green |
| tests/test_bug_94_real_mic.py | #94 | quiet mic detected and cut at pauses; final tail never trimmed; owner wav regression (≥5 pause cuts, speech ≥25 s, end ≥40 s) | unit + S-tier fixture (log/, not in git) | green |
| tests/test_bugs_96_97.py | #96 #97 | token cap grows with audio; restore delay ≥ 1 s | unit | green |
| #96 short final chunk loop | Regression: passage 004 final chunk final_asr_ms < 800, repeats < 10 | pending owner run |
| #97 English text inserted | Regression: paste into Claude Code with English on the clipboard beforehand → Hinglish lands | pending owner run |
| tests/test_bug_94_real_mic.py (3 owner recordings) | #94 #99 | quiet mic, clean mic, noisy input: ≥5 pause cuts each, tail kept, ≤1 s trimmed | S-tier fixtures (log/, not in git) | green |
| #99 noisy input hides pauses | Regression: owner wav 190404 ≥ 5 pause cuts | working (unit); owner live pending |

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

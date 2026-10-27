# Experiments

Every open claim becomes a hypothesis with a test. Rows are never deleted.

| Id | Hypothesis | Design | Decision rule | Start | Result | Decision |
|---|---|---|---|---|---|---|
| H1 | whisper-tiny LID separates Indian-accented English from Hinglish well enough to route | 12 fixture clips (2 TTS English incl. Indian voice, 2 TTS Hindi/Hinglish, 8 real human Hindi/Hinglish from the Apex repo), 5 runs each, record p(en) | both English clips p(en) ≥ 0.8 and all Hindi clips < 0.8 → MODE=auto ships; else two keys | 2026-10-07 | English 0.96 and 1.00; Hindi/Hinglish 0.00 to 0.43 (max 0.43 on two short real clips). lid 40 to 90 ms, 181 ms on a 12.5 s clip | **MODE=auto ships.** Threshold 0.8 has margin both ways. Still to confirm on the owner's own voice (S-tier) |
| H2 | Apex English quality is close to base turbo | English clip through Apex and mlx-community/whisper-large-v3-turbo, compare by ear and WER on 5 sentences | on par → router can lean on Apex; else router threshold stays 0.8 and Parakeet handles clear English | 2026-10-07 | Apex on both TTS English clips: word-perfect, same as Parakeet. Turbo comparison not run (not needed: Apex already matches) | Router keeps 0.8; Apex is a safe fallback for English. Side finding: Parakeet on Hindi audio is garbage ("May not the poor can"), so the router is a must, not a nice-to-have |
| H3 | mlx-whisper Apex q8 on M1 8 GB gives Hinglish p50 < 1.2 s on a 5 s clip | bench.py, Apex alone, 3 runs, 12 clips | pass → ship; else q4; else pywhispercpp + CoreML encoder | 2026-10-07 | **4.9 to 6.3 s on every clip, flat from 1.0 s to 12.5 s of audio** (swap 5.6 GB in use). Flat means the 30 s padded encoder is the whole cost, not the decoder | **Fail.** Follow-up H3b: Apex fp16 (quantized matmul may be slow on a 1500-token encoder), MLX encoder with a 10 s / 15 s window (sliced sinusoid table, same as whisper.cpp audio_ctx), whisper.cpp Metal q8 with audio_ctx |
| H4 | parakeet-mlx on M1 gives English p50 < 0.7 s on a 5 s clip | bench.py, Parakeet alone, 3 runs | pass → ship; else report the number | 2026-10-07 | 446 ms (4.7 s clip), 481 ms (5.3 s), 178 ms (1.0 s), 1010 ms (12.5 s). Under swap pressure | **Pass.** |
| H5 | AX set inserts correctly in TextEdit, Chrome, VS Code, Terminal, Slack | manual matrix | any silent failure → paste for all apps | pending | | |
| H6 | CT2 int8 Apex on a 4-thread CPU proxy is under 2.0 s for a 5 s clip | bench.py with OMP_NUM_THREADS=4, no GPU | pass → faster-whisper on Windows; else pywhispercpp + GGML q5 + audio_ctx=768 | pending | | |
| H7 | Swift q8 GGML on the proxy is under 1.0 s and usable by ear | same | pass → micro profile ships; else micro = lean with a 4 GB warning | pending | | |
| H8 | Three models resident stay under 2.5 GB on M1 | /usr/bin/time -l during bench | pass → full profile; else q4 Apex | 2026-10-07 | max RSS 1.14 GB, but MLX unified-memory buffers are not in RSS, so this understates it. With all three loaded and 5.6 GB swap already in use, Parakeet went from 0.45 s alone to 4 to 28 s: the machine was paging | Inconclusive on a loaded machine. Re-measure with Chrome and FluidVoice closed; add `mx.get_peak_memory()` to bench.py |

## Bench run 2026-10-07 (M1 8 GB, RUNS=5, tiny fp16 / parakeet bf16 / apex q8)

| clip | s | p(en) | lid ms | parakeet p50 | p90 | apex p50 | p90 |
|---|---|---|---|---|---|---|---|
| apex_663eb653_d6b5_4fda_b | 1.3 | 0.06 | 40 | 212 | 1040 | 4504 | 4881 |
| apex_c0637211_7384_4abc_a | 1.7 | 0.03 | 66 | 408 | 6607 | 4612 | 4690 |
| apex_c0faba11_27ba_4837_a | 2.7 | 0.43 | 70 | 313 | 1506 | 3927 | 4381 |
| apex_common_voice_hi_2379 | 4.7 | 0.02 | 46 | 371 | 1221 | 3981 | 4360 |
| apex_common_voice_hi_4090 | 6.7 | 0.01 | 42 | 759 | 2213 | 5210 | 5210 |
| apex_common_voice_hi_4142 | 7.6 | 0.00 | 58 | 560 | 1914 | 4508 | 4845 |
| apex_common_voice_hi_4166 | 12.5 | 0.04 | 181 | 861 | 2772 | 3896 | 3960 |
| apex_f5e0178c_354c_40c9_b | 1.0 | 0.43 | 41 | 320 | 941 | 3737 | 3972 |
| english_in | 5.3 | 0.96 | 90 | 10294 | 20868 | 6203 | 6637 |
| english_us | 4.7 | 1.00 | 71 | 4495 | 11619 | 6061 | 6696 |
| hindi_tts | 4.5 | 0.04 | 73 | 25453 | 28997 | 6666 | 6917 |
| hinglish_tts | 4.7 | 0.02 | 46 | 674 | 2305 | 9434 | 12376 |

## Bench run 2026-10-07 (M1 8 GB, RUNS=3, ONLY=['apex'], tiny fp16 / parakeet bf16 / apex q8; swap used 4750.38M)

| clip | s | p(en) | lid ms | parakeet p50 | p90 | apex p50 | p90 |
|---|---|---|---|---|---|---|---|
| apex_663eb653_d6b5_4fda_b | 1.3 | nan | nan | nan | nan | 6322 | 6322 |
| apex_c0637211_7384_4abc_a | 1.7 | nan | nan | nan | nan | 5540 | 5540 |
| apex_c0faba11_27ba_4837_a | 2.7 | nan | nan | nan | nan | 5286 | 5286 |
| apex_common_voice_hi_2379 | 4.7 | nan | nan | nan | nan | 5395 | 5395 |
| apex_common_voice_hi_4090 | 6.7 | nan | nan | nan | nan | 5559 | 5559 |
| apex_common_voice_hi_4142 | 7.6 | nan | nan | nan | nan | 5221 | 5221 |
| apex_common_voice_hi_4166 | 12.5 | nan | nan | nan | nan | 5350 | 5350 |
| apex_f5e0178c_354c_40c9_b | 1.0 | nan | nan | nan | nan | 5041 | 5041 |
| english_in | 5.3 | nan | nan | nan | nan | 5048 | 5048 |
| english_us | 4.7 | nan | nan | nan | nan | 4950 | 4950 |
| hindi_tts | 4.5 | nan | nan | nan | nan | 5127 | 5127 |
| hinglish_tts | 4.7 | nan | nan | nan | nan | 5681 | 5681 |

## Bench run 2026-10-07 (M1 8 GB, RUNS=3, ONLY=['parakeet'], tiny fp16 / parakeet bf16 / apex q8; swap used 5413.44M)

| clip | s | p(en) | lid ms | parakeet p50 | p90 | apex p50 | p90 |
|---|---|---|---|---|---|---|---|
| apex_663eb653_d6b5_4fda_b | 1.3 | nan | nan | 316 | 316 | nan | nan |
| apex_c0637211_7384_4abc_a | 1.7 | nan | nan | 254 | 254 | nan | nan |
| apex_c0faba11_27ba_4837_a | 2.7 | nan | nan | 451 | 451 | nan | nan |
| apex_common_voice_hi_2379 | 4.7 | nan | nan | 430 | 430 | nan | nan |
| apex_common_voice_hi_4090 | 6.7 | nan | nan | 455 | 455 | nan | nan |
| apex_common_voice_hi_4142 | 7.6 | nan | nan | 668 | 668 | nan | nan |
| apex_common_voice_hi_4166 | 12.5 | nan | nan | 1010 | 1010 | nan | nan |
| apex_f5e0178c_354c_40c9_b | 1.0 | nan | nan | 178 | 178 | nan | nan |
| english_in | 5.3 | nan | nan | 481 | 481 | nan | nan |
| english_us | 4.7 | nan | nan | 446 | 446 | nan | nan |
| hindi_tts | 4.5 | nan | nan | 567 | 567 | nan | nan |
| hinglish_tts | 4.7 | nan | nan | 421 | 421 | nan | nan |

## Bench run 2026-10-07 (M1 8 GB, RUNS=3, ONLY=['lid', 'parakeet', 'apex'], tiny fp16 / parakeet bf16 / apex q8; swap used 6082.94M)

| clip | s | p(en) | lid ms | parakeet p50 | p90 | apex p50 | p90 |
|---|---|---|---|---|---|---|---|
| apex_663eb653_d6b5_4fda_b | 1.3 | 0.06 | 47 | 819 | 819 | 5863 | 5863 |
| apex_c0637211_7384_4abc_a | 1.7 | 0.03 | 119 | 7156 | 7156 | 6262 | 6262 |
| apex_c0faba11_27ba_4837_a | 2.7 | 0.43 | 59 | 7006 | 7006 | 6060 | 6060 |
| apex_common_voice_hi_2379 | 4.7 | 0.02 | 91 | 11199 | 11199 | 6217 | 6217 |
| apex_common_voice_hi_4090 | 6.7 | 0.01 | 69 | 10641 | 10641 | 6264 | 6264 |
| apex_common_voice_hi_4142 | 7.6 | 0.00 | 139 | 5169 | 5169 | 5428 | 5428 |
| apex_common_voice_hi_4166 | 12.5 | 0.04 | 195 | 4498 | 4498 | 19528 | 19528 |
| apex_f5e0178c_354c_40c9_b | 1.0 | 0.43 | 145 | 9520 | 9520 | 8772 | 8772 |
| english_in | 5.3 | 0.96 | 81 | 21181 | 21181 | 8353 | 8353 |
| english_us | 4.7 | 1.00 | 140 | 27860 | 27860 | 6346 | 6346 |
| hindi_tts | 4.5 | 0.04 | 140 | 3598 | 3598 | 5282 | 5282 |
| hinglish_tts | 4.7 | 0.02 | 125 | 1562 | 1562 | 4866 | 4866 |

| H3-live | Lean profile with the 5 s-step window is fast enough in daily use | Owner's first live session, 5 dictations, stats.jsonl | English/Hinglish under 1.2 s for short clips; long clips reported | 2026-10-07 | 2.8 s clip → 0.86 s; 10 to 12 s → 2.3 s; 24 s / 95 words → 5.1 s. About 0.2 s per spoken second, linear. One 11 s clip gave 1 word (cause unknown, owner to say what was spoken) | Short dictation meets the target; long ones scale linearly. Accuracy: small slips ("transparai"), owner calls it fine for v1. Insertion failed inside Claude Code in the terminal: AX reported success, nothing inserted (R4 confirmed). Fix: AXUIElementIsAttributeSettable check before AX, else paste |
| H9 | Transcribing while talking brings release-to-text under 1 s p50 / 1.5 s p90 for any dictation up to 60 s (ADR-013) | spot_stream.py real-time feed on a 38.6 s synthetic Hinglish clip, then the owner's live dictations via tools/report.py | targets met → ship; else decision table in the plan | 2026-10-07 | Baseline 24 s → 5.5 s. After: 38.6 s → 811 to 1131 ms (final chunk 504 to 823 ms, wait 0, rtf 0.22). Bugs found and fixed on the way: #88 tight window → nan, #89 loop | **Pass on synthetic**; owner live (T11) pending. Lever if p50 slips: lower MIN_CHUNK_S so the final chunk is shorter |

## Pending: Apex Hinglish in Handy (whisper.cpp) vs Bhavna (MLX), added 2026-10-09
- Hypothesis: Handy's engine (whisper.cpp Metal) runs `ggml-apex-hinglish-q8_0.bin` within 20% of Bhavna's MLX speed on this Mac. My guess: no, about 2 times slower (ADR-003). Confidence 0.6.
- Design: both engines, same 13 clips in `tests/fixtures`, RUNS=5, p50 and p90 release-to-text, same text check.
- Needs: `brew install whisper-cpp`; Bhavna stopped for 5 minutes (8 GB RAM).
- Decision: within 20% -> AI Assistant uses Handy's engine. Slower -> Handy UI plus Bhavna MLX engine on Mac.
- Status: parked by Satvik. Not run yet.

## 2026-10-27: cascade scheduler on logged timing, no model run (E12, plan scalable-orbiting-lemon, #110 #112 #113)
- Hypothesis (H-cascade-1): picking Swift, Apex or Prime per chunk from slack cuts release-to-text p90 without a worse p50.
- Design: `tools/simulate.py` replays the chunk timing of 592 logged dictations through one FIFO worker. Lean uses each chunk's real decode time. Other models are Apex's time times a ratio (swift 0.15 to 0.3, prime 1.2 to 3), because Swift and Prime are not measured yet. Apex chunk RTF p50 is 0.46 (p90 1.21).
- Check of the tool: simulated lean p50 1.92 s, p90 10.15 s. Measured lean p50 2.57 s, p90 11.28 s. About 0.6 to 1.1 s optimistic.
- Result 1: with the median talk time left as slack, the cascade is worse than lean (likely scenario p50 4.31 s, p90 15.2 s). Prime took 83% of the audio and the backlog piled up. His talk-length history is flat (about 22 s left at every point), so the median slack is always large.
- Result 2: with the 10th percentile as slack (`SLACK_Q = 0.1`) the cascade gives p50 1.5 to 1.9 s and p90 5.9 to 8.7 s, with 18% to 66% of the audio on Prime. p90 is better than lean in all three scenarios; p50 is about the same.
- Not met: targets B1 (p50 under 1.0 s) and B2 (p90 under 1.5 s). The scheduler alone cannot reach them. The slow cases are big final chunks and busy-machine decode times. Next ideas, in order: shorter last chunk at release (a), early decode at the first pause (b), then a smaller Apex window.
- Caveat: the simulator knows speed, not accuracy. "All Swift" is fastest and worst. The model mix is only a proxy. WER per model (T2.5) decides whether Prime is worth its share.
- Decision: keep `SLACK_Q = 0.1`. The real run waits for the owner's yes to load models on the Mac. T2.4 numbers replace the guessed ratios. Not decided: whether to ship the cascade at all (Phase 6).

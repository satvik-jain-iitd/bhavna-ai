# Experiments

Every open claim becomes a hypothesis with a test. Rows are never deleted.

| Id | Hypothesis | Design | Decision rule | Start | Result | Decision |
|---|---|---|---|---|---|---|
| H1 | whisper-tiny LID separates Indian-accented English from Hinglish well enough to route | 4 mic clips (en, Indian en, Hinglish, Hindi), 5 runs each, record p(en) | both English clips p(en) ≥ 0.8 and both Hindi clips < 0.8 → MODE=auto ships; else two keys | pending | | |
| H2 | Apex English quality is close to base turbo | English clip through Apex and mlx-community/whisper-large-v3-turbo, compare by ear and WER on 5 sentences | on par → router can lean on Apex; else router threshold stays 0.8 and Parakeet handles clear English | pending | | |
| H3 | mlx-whisper Apex q8 on M1 8 GB gives Hinglish p50 < 1.2 s on a 5 s clip | bench.py, 5 runs | pass → ship; else q4; else pywhispercpp + CoreML encoder | pending | | |
| H4 | parakeet-mlx on M1 gives English p50 < 0.7 s on a 5 s clip | bench.py, 5 runs | pass → ship; else report the number | pending | | |
| H5 | AX set inserts correctly in TextEdit, Chrome, VS Code, Terminal, Slack | manual matrix | any silent failure → paste for all apps | pending | | |
| H6 | CT2 int8 Apex on a 4-thread CPU proxy is under 2.0 s for a 5 s clip | bench.py with OMP_NUM_THREADS=4, no GPU | pass → faster-whisper on Windows; else pywhispercpp + GGML q5 + audio_ctx=768 | pending | | |
| H7 | Swift q8 GGML on the proxy is under 1.0 s and usable by ear | same | pass → micro profile ships; else micro = lean with a 4 GB warning | pending | | |
| H8 | Three models resident stay under 2.5 GB on M1 | /usr/bin/time -l during bench | pass → full profile; else q4 Apex | pending | | |

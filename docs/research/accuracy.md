# Accuracy: read-aloud sessions (S9.0)

Owner reads a passage exactly; the dictation is scored against it with `tools/wer.py`. S-tier.

| Date | Passage | Words | WER | Errors | Gaps (reference → heard) | Notes |
|---|---|---|---|---|---|---|
| 2026-10-07 17:58 | 001 compound interest | 111 | 35.1% strict | 39 | spelling variants: rupaye→rupe, pehle→pahle, tumhare→tumhaare, sirf→sirph, nahi→nahin, tumhe→tumhen, zyada→zyaada; real: byaaj→pyaaj, dus→das, chakravriddhi→chakr vrddhi; speaker self-corrections kept (ho jaenge ho jaega, pachaas pachchis) | 23 deletions = the tail dropped by bug (chunker trim). Excluding the tail: 16 / 88 = 18%, of which ~7 are spelling conventions → dictionary candidates |

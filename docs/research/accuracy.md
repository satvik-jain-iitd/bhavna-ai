# Accuracy: read-aloud sessions (S9.0)

Owner reads a passage exactly; the dictation is scored against it with `tools/wer.py`. S-tier.

| Date | Passage | Words | WER | Errors | Gaps (reference → heard) | Notes |
|---|---|---|---|---|---|---|
| 2026-10-07 17:58 | 001 compound interest | 111 | 35.1% strict | 39 | spelling variants: rupaye→rupe, pehle→pahle, tumhare→tumhaare, sirf→sirph, nahi→nahin, tumhe→tumhen, zyada→zyaada; real: byaaj→pyaaj, dus→das, chakravriddhi→chakr vrddhi; speaker self-corrections kept (ho jaenge ho jaega, pachaas pachchis) | 23 deletions = the tail dropped by bug (chunker trim). Excluding the tail: 16 / 88 = 18%, of which ~7 are spelling conventions → dictionary candidates |
| 2026-10-07 18:20 | 004 Jev | 184 | 31.0% strict | 57 | conventions: woh→vah, yeh→yah, nahi→nahin, liye→lie, dheere→dhire, joined "dekh kar"→dekhakar; numbers: one→1, two→2, 2026→"20 20 26"; real: Daniel→Annual, Jev→jayab/jab/jeb, TypeSafe AI→"type se", schema→schhima, field→fees, sattar→saptaah, prose→pros, typed→tied, bekaar→mekaar, Jevons→javaan | New engine: 9 chunks, 8 pause cuts, full text. Final short chunk looped (bug logged). Product names and English jargon are the real gap → dictionary |
| 2026-10-07 19:04 | 005 terminal | 171 | 26.9% strict | 46 | conventions: seekh→sikh, nahi→nahin, pehle→pahle, liye→lie, beech→beach, cheez→chiz, kuch→kuchh, yeh→yah, bahar→baahar, khatam→khatm; real: Terminal→Mainna, "control E"→dropped, "control U"→"Toll yu", "up arrow"→aapero, ls→Celes, "sakte ho"→dropped | New engine after #98: 6 chunks but 0 pause cuts, 5 forced (floor stuck low, everything read as speech); release→text 1550 ms; insert 18 ms, no English; repeats 0 |

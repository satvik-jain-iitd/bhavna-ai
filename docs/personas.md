# Users: personas and prioritisation

<!-- Source: docs/PLAN.md. Edit there, then re-split. -->

### A4. Users: personas, jobs, prioritisation

**P1. The bilingual knowledge worker (primary, v1).** Works in India, writes into Claude, Slack,
docs and WhatsApp Web all day. Speaks Hinglish without thinking about it. Owns an M-series Mac or a
mid-range Windows laptop at home and a locked-down laptop at work. Has paid for tools and dropped
them for speed. Job: "When I have a thought, get it into the box in front of me before I lose it,
in the words I said." Pain: the Hindi lag breaks the flow, tools rewrite the words, nothing runs on
the work laptop. Success: they stop thinking about the tool.
User zero (Satvik) is this persona: M1 Air 8 GB at home, Windows laptop at the company.

**P2. The company-laptop worker (v2).** Windows, 8 GB, no GPU, IT blocks downloads and installers.
Types Roman Hindi on WhatsApp all day. Job: "Dictate a message or a ticket the way I would type
it." Needs: zip install, no admin rights beyond Python, CPU speed.

**P3. The Hindi-first creator or ops person (v3).** Cheapest Windows laptop, 4 GB. Comfortable with
Roman Hindi, weak with English spelling. Job: "Say it in Hindi, get it in Roman letters so my
phone-typing friends read it." Needs: the micro profile, forgiving accuracy, zero setup.

**Not for:** native English speakers (Parakeet-only tools serve them already). Devanagari writers
(a different product). Meeting transcription (long-form, a different latency shape).

Prioritisation: P1 first, because user zero is P1 and can measure daily. P2 second, because user
zero also owns that laptop. P3 sets the floor hardware profile and the accuracy bar.

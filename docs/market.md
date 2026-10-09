# Market, competitors, industry

<!-- Source: docs/PLAN.md. Edit there, then re-split. -->

### A2. Market and competitor research

Sources are vendor pages and open-source repos. Vendor claims are Tier C unless the code is open
(Tier A for the mechanism). Latency numbers are theirs unless marked.

| Product | Runs | Price | Hindi / Hinglish | Insert method | Bloat | Open |
|---|---|---|---|---|---|---|
| Wispr Flow | cloud ASR, mac/win | $12/mo | Hindi yes; Roman output not documented | Accessibility API | LLM cleanup always on | no |
| Superwhisper | local whisper + cloud, mac | $8.49/mo or $249 | Hindi via whisper, Devanagari, slow | paste | AI modes, GUI | no |
| FluidVoice | local (Parakeet CoreML, WhisperKit), mac | free | Parakeet v3 has no Hindi; whisper path is Devanagari | AX set + paste fallback (code read) | LLM "Fluid-1" polish, menu bar | GPLv3 |
| VoiceInk | local, mac | $25 once or build free | whisper, Devanagari | paste | AI enhancement, GUI | yes |
| Handy | local (whisper, Parakeet), mac/win/linux | free | whisper, Devanagari | clipboard paste (enigo) | Tauri GUI | MIT |
| OpenWhispr | local + cloud, cross | free | whisper, Devanagari | paste | Electron GUI | MIT |
| Musely | cloud, mac | subscription | Hindi slow (user zero's test) | paste | GUI, AI | no |
| macOS / Windows built-in | local or cloud | free | Hindi yes, Devanagari, no Hinglish | native | none | no |
| Gboard voice (phone) | cloud or on-device | free | Hinglish OK | native | none | no |

What every row shares: Hindi means Devanagari, and Devanagari means the token tax. None ships a
Roman-Hinglish model. None bundles weights for locked-down laptops. Most add an LLM pass the user
cannot fully switch off.

What we borrow: AX insertion with paste fallback (FluidVoice), hold-to-talk on one key (Wispr),
Parakeet for English (FluidVoice, Handy), p90 as the number that matters (Wispr's CTO).

### A3. Industry research (what is moving under this product)

- **Models are getting smaller and better.** A 0.6 B model (Parakeet) now beats a 1.5 B model
  (whisper-large) on English. Expect the same for Indic within a year (AI4Bharat, Oriserve, Sarvam
  are all publishing). Architecture rule: a model is a folder in `models/`, swappable.
- **Tokenizer cost is the hidden Indic bottleneck.** Papers (ICASSP 2025) and maintainers (a
  WhisperKit issue) both measure about 2.5x. Expect Indic-tokenizer models soon. Until then, Roman
  output.
- **On-device is the default for sensitive work.** Company laptops block cloud AI and Hugging Face.
  Bundled weights are a feature, not a workaround.
- **Apple Silicon only, going forward.** Rosetta ends at macOS 28 (Apple article 102527). Intel Mac
  support is dead weight. MLX is the Apple-native Python path; CoreML on the Neural Engine is faster
  still but Swift-only.
- **Windows is a CPU story for most Indian laptops.** The cheapest machines have 4 to 8 GB and an
  integrated GPU. int8 ONNX and whisper.cpp's shortened encoder window are the tools that fit.
- **Code-switched speech is an open research gap.** Public Hinglish data is small (HiACC, 5 h) or
  synthetic. A user's own corrections are the most valuable data. That is the self-learning lever.

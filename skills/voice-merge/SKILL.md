---
name: voice-merge
description: Build a merged target "voice" (VOICE.md style card) for a writing task from several recent primary papers on the same topic in Nature/Cell/Science and their allowed research sub-journals, then hand it to the writer agent. Use before writing a report/paper section when the user has no voice sample of their own.
---
# Voice merge
Goal: a style card (features, not text) the writer imitates. Output: `reference/voice/VOICE.md` in the project, shown to the user once for approval.
1. **Find** (reader agent, PubMed/Consensus MCP): 5-8 primary research papers on the topic, published in the last ~3 years, only in journals in `journals.md`. Journal name comes from PubMed metadata; reject anything not on the list and say what was rejected. Order by relevance, not impact.
2. **Read** (reader agent; full text only if open access, else abstract + Results opening from PubMed/Europe PMC; never paywall scraping). Add each to `lit-kb` (`kb.py add`).
3. **Profile each paper** (quantitative where possible): sentence-length median/p90, paragraph length, tense by section, "we" vs passive, hedge verbs and where they sit, how Results paragraphs open and close, how numbers/CIs/p-values are written, figure-callout style, Introduction arc, gloss habits for methods, Discussion limitations style, vocabulary to avoid.
4. **Merge**: keep features shared by >=3 papers as RULES; features seen in 1-2 papers as OPTIONAL; conflicts resolved by the stricter/more precise option. Write `VOICE.md` (<=1.5 pages) with the citekeys and journal for each paper.
5. **Hard limits (copyright, accuracy)**: VOICE.md contains style descriptions and at most short (<=8 words) generic phrase patterns, never sentences or paragraphs copied from the papers; no facts, numbers, or claims from those papers enter the writer's text. The writer imitates structure and register, never wording.
6. Writer call: `writer_delegate.py "<brief>" --voice reference/voice/VOICE.md -c facts.md`. Writer notes must state which VOICE rules were applied; user's own papers, if later supplied, override the merged voice.
Precedence: facts/accuracy rules > user's own voice sample > merged VOICE.md > academic-humanizer defaults. Humanizer Layer 3 (never alter numbers/citations; no em-dashes) always wins over imitation.

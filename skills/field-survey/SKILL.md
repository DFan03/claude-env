---
name: field-survey
description: Pre-research for ANY project, before designing methods. Review-first literature survey with citation-frequency must-reads and an explicit "enough" test. Use at project start and when entering a new sub-problem; produces reference/golden_standard/FIELD_SURVEY.md for user approval.
---

# field-survey (any project, any field)
Goal: know how the best people in this field do this kind of work, and how they present it, BEFORE designing.
Never judge by number of papers. Judge by whether the Enough Test below passes.

## Steps (parallel architecture)
Stage 0 - **Question list** (`reference/golden_standard/SURVEY_QUESTIONS.md`), written before searching. Always include:
Q-workflow, Q-tools (+failure modes), Q-stats (null models/controls), Q-validation (what counts as proof, controls),
Q-bias (leakage, confounding, redundancy), Q-present (standard figures/tables), Q-exemplar, plus project-specific ones.
Stage A - **Coordinator agent(s)** (a few, in parallel, e.g. one per sub-area/layer): find 3-5 recent reviews per area plus
benchmark/critique and statistics/method papers; extract their reference lists into `reference/literature/citation_pool.tsv`
(paper, #sources citing it, year). Output `MUST_READ.tsv`: papers cited by >=3 sources, original papers of every tool/method
planned, 2-3 exemplar papers, and the key statistics/method papers. Coordinators only select; they do not read in depth.
Stage B - **Targeted search-reading, never first-to-last-word** (DeepSeek flash only, never Claude subagents; user rules).
The reader is driven by the written question list (SURVEY_QUESTIONS.md, Q-ids). Per paper, escalate only while it pays off:
 B0 *Citation-context triage* (local, no LLM): in the reviews already read, take the sentence(s) that cite the paper ("cited for").
    A paper cited only for a topic outside the question list is dropped here; its cited-for line is kept in the note.
 B1 *Abstract triage* (flash on abstract + cited-for line + questions): returns JSON {relevant: yes/no, answers_qids: [..],
    reason}. No Q-id matched -> SKIP, write a 3-line stub note (skipped, reason). Abstract-only is allowed when it fully answers.
 B2 *Heading triage* (local keyword match on section titles/figure legends, flash only if ambiguous): choose the sections that can
    hold each matched Q-id. If no section can, STOP: do not read the full text.
 B3 *Targeted read* (flash on the chosen sections only): per Q-id give the answer with exact quote, or "not found". Add Methods only
    when the Q-id is about how something was measured. Note tag lists what was read: [cited-for] [abstract] [sections: ...].
 B4 *Escalate to full text* only if a must-read (cited by >=3 sources, a tool/method original, or an exemplar) AND B3 returned "not found" for a matched Q-id.
Notes are per Q-id (answer, quote, section), not a generic 8-line summary. Log per paper: stage reached, tokens, skipped y/n.
Stage B must report the skip rate and a spot-check: re-read 5 skipped papers in full; if >=1 held a needed answer, loosen B1.
Tool: tools/ds_triage.py (project copy of ~/.claude/tools/ds_triage.py). Readers add the paper via `kb.py add` (metadata from PubMed/Crossref only).
Stage C - **Snowball**: new must-reads found by readers (cited by >=3 sources) go back to Stage B (new readers) until saturation.
Stage D - **Synthesizer** (one agent or main session) reads the per-paper notes only and writes
`reference/golden_standard/FIELD_SURVEY.md` (<=150 lines): per question the answer with citekeys, disagreements, what we
do differently and why, concrete design recommendations. Then a skeptical PI-persona pass ("what is missing?").
Log every query in `search_log.md` (date | query | source | hits | kept | why). Show FIELD_SURVEY.md to the user for approval.
Main session keeps only conclusions + paths, never paper text.

## Enough Test (all must hold; write the check in FIELD_SURVEY.md)
- [ ] Every question in SURVEY_QUESTIONS.md has an answer backed by >=2 independent sources (>=1 full-text).
- [ ] Every paper cited by >=3 pooled sources is read (full text) or explicitly excluded with a reason.
- [ ] Original papers of all tools/methods we plan to use are read.
- [ ] >=2 exemplar papers reviewed for presentation; a figure/table template list exists.
- [ ] Saturation: the last 3 searches / snowball steps found no new tool, method, pitfall or must-read.
- [ ] Disagreements between sources are listed, not smoothed over.
- [ ] A skeptical reviewer persona (pi-review style) asked "what is missing?" and the gaps are closed or listed.
If any box is unchecked, keep researching or state the gap openly in FIELD_SURVEY.md; do not call it done.
Delegate reading to DeepSeek pro via paper-digest (verify quoted numbers against source). Offload searching to a
subagent only with this protocol in the brief; never with a paper-count target.

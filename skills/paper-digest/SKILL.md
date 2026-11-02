---
name: paper-digest
description: Offload paper/long-document reading to DeepSeek flash (1M context) and get a structured, citation-checked summary. Use for literature review or building golden-standard SUMMARY.md files.
---
# Paper digest
1. Convert PDFs to text (`pdftotext -layout x.pdf x.txt`, or the pdf skill).
2. Do not send whole papers by default: use the staged search-reading of the field-survey skill (cited-for, abstract, headings, targeted sections). Whole-text reads only for escalated must-reads.
   Run (parallel across papers is fine, one call per paper):
   `python3 ~/.claude/tools/deepseek_delegate.py "<prompt>" --model flash -c x.txt --max-tokens 4000`
   Prompt must request: (a) 10-line summary; (b) actionable methodological rules, each with page/section; (c) exact quotes for every number/threshold; (d) "NOT STATED" when absent. No inference.
3. Verify: grep each quoted number/quote in the source text. Drop anything unverifiable.
4. Write `SUMMARY.md` beside the source; show the user for approval before relying on it (CLAUDE.md rule).
5. Never let DeepSeek make method decisions; it only extracts.
6. Store results in the project KB via the `lit-kb` skill (`kb.py add`, then fill the paper note).

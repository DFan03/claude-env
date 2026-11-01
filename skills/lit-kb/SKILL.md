---
name: lit-kb
description: Per-project literature knowledge base (reference/literature/). Use BEFORE answering any scientific/method question or decision (search it), and WHENEVER a new paper is found or used (add it). Gives citable BibTeX plus human-readable per-paper notes.
---
# Literature knowledge base
Location: `reference/literature/` in each project (commit it to git).
- `papers/<citekey>.md`: frontmatter (title, authors, year, journal, doi, pmid, status, tags, used_in) + Summary / Key findings (with page) / What we use from it / Verified quotes.
- `library.bib`: BibTeX, auto-generated from the papers. Cite with the citekey (authorYYYYword, e.g. smith2020rna).
- `INDEX.md`: readable table, auto-generated. Start here.
- `search_log.md`: append one line per search: date, query, source, #hits, what was kept.
Tool: `python3 ~/.claude/skills/lit-kb/kb.py [--root reference/literature] add|find|check|index|bib`

Rules (always):
1. **Before** answering a science/method question or making a decision: `kb.py find <term>` and read `INDEX.md`; cite citekeys in the answer. If the KB is silent, say so, then search.
2. **Search** with PubMed/bioRxiv/Consensus tools; log in search_log.md.
3. **Add** every paper that is used or likely relevant: take metadata (DOI, authors, year) from PubMed/Crossref results, never from memory; run `kb.py add`.
4. **Summarize** via `paper-digest` (DeepSeek pro reads; I verify numbers/quotes against the source). Fill Summary, Key findings, What we use from it. Set status `summarized`; `verified` only after quotes/numbers are checked in the source. Show user new summaries for approval.
5. When a decision uses a paper, set `used_in` and name the paper in methods.md.
6. Before writing a paper or reporting: `kb.py check` must pass; flag any `to-read` paper cited.

## Papers the user names (title / DOI / URL) = MUST include
- Always add them to the KB with tag `user-provided`, even if they seem marginal; never drop them.
- Title only -> resolve DOI via PubMed / Crossref / OpenAlex; confirm match (title + first author + year).
- Full-text retrieval chain (legal sources only; never Sci-Hub or other piracy sites):
  1. `python3 ~/.claude/skills/lit-kb/fetch_oa.py <DOI|URL> --key <citekey>` -> tries OpenAlex OA locations
     (publisher OA, repositories), Europe PMC / PMC PDF, then PMC full-text XML. Prefers the published
     version; a saved preprint is flagged `PREPRINT` -> note "preprint version" in the paper note.
  2. PubMed MCP `get_full_text_article`, bioRxiv/medRxiv MCP, Consensus (for related OA versions).
  3. Author-hosted copies (lab page, ResearchGate/Academia author uploads, institutional repository) via WebSearch.
  4. Nothing works -> ask the user ONE line: "Please drop the PDF of <citekey> (<title>) into
     reference/literature/pdfs/<citekey>.pdf (library access / interlibrary loan / ask the author)."
     Meanwhile, summarize from the abstract only and mark the note `status: to-read (abstract only)`.
- PDFs/XML live in `reference/literature/pdfs/` and are git-ignored (copyright); notes + bib are committed.

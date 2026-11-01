---
name: feedback-offtheshelf-and-rationale
description: User wants established tools/published methods over home-made code, every method choice logged with rationale, and a human-readable GitHub README for final review
metadata:
  type: feedback
---

Prefer off-the-shelf libraries/methods that are used in relevant research (or at least follow their computational logic) instead of writing my own.
Every method choice needs a stated rationale, logged in the workflow (docs/DECISIONS.md in rna_motif) and summarized in a human-readable README.md on GitHub, which the user reviews at the end.

**Why:** user reviews the whole project at the end and wants it defensible and reproducible, not ad hoc.
**How to apply:** before writing code, check for an established tool (bioconda/pip); add a row to DECISIONS.md with reason + alternatives; keep README current; push commits to the private GitHub repo DFan03/rna_motif (see [[project-rna-motif]]).

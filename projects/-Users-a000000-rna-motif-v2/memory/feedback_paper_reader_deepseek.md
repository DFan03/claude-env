---
name: feedback-paper-reader-deepseek
description: "Per-paper reading in literature surveys must use DeepSeek pro (1M ctx), never Claude/Sonnet subagents"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 1d82f857-70e4-408b-8a59-7a8b1d1d90cf
  modified: 2026-11-02T04:24:51.578Z
---

Paper readers (field-survey Stage B, one reader per paper) must be DeepSeek (flash is fine and cheaper; user allowed it 2026-11-02) via `deepseek_delegate.py --model flash`, not Claude/Sonnet subagents.

**Why:** User corrected this twice in v3 after I launched Sonnet reader agents for batches 1-4 (40 papers); they want Claude tokens kept for planning/integration and DeepSeek for bulk reading.

**How to apply:** use `/Users/a000000/rna_motif_v3/tools/ds_read.py citekey pmid FULL|ABS` (xargs -P 12). Use --max-tokens 32000 (8000 truncates to empty with the reasoning model; ~2 min per paper). See [[paper-digest]] skill.

---
name: no-deepseek-pro
description: From 2026-11-09 user said DeepSeek pro was used at unreasonable speed; pro-type tasks (paper reading, extraction, pass 2) go to Claude API instead
metadata:
  type: feedback
---

User (2026-11-09): "You've been using deepseek pro at a unreasonable speed, for deepseek pro tasks from now on use Claude API".

**Why:** DeepSeek spend (200+ CNY in a day, repeated top-ups) alarmed them.
**How to apply:** Use `claude_delegate.py` (sonnet for reading/extraction, opus for critical judgement) for work I'd have sent to `--model pro`. DeepSeek flash for cheap bulk screening is not mentioned by this rule. Estimate cost first. See [[feedback_use-claude-api-more]], [[feedback_budget-quality-over-cost]].

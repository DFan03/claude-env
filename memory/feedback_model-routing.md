---
name: feedback-model-routing
description: Route self-contained work to Claude API credit (claude_delegate.py) by task; DeepSeek flash only for cheap bulk work; no DeepSeek pro
metadata:
  type: feedback
---

User (2026-11-09): use Claude API credit more (Agent-tool subagents bill the scarcer Claude Code balance), and "You've been using deepseek pro at a unreasonable speed, for deepseek pro tasks from now on use Claude API".

**Why:** Claude Code balance is scarce, API credit is large; DeepSeek spend (200+ CNY in a day) alarmed them.
**How to apply:** Opus via API = stats/method review, PI review, adjudication; Sonnet via API = new/complex code, reading and extraction that would have gone to DeepSeek pro; writer_delegate.py for prose; DeepSeek flash = routine bulk extraction/screening only. Use Agent-tool subagents only when tools/repo access are needed. Check the [claude_usage] trailer (served == requested). Estimate cost first. See [[feedback-budget-quality-over-cost]].

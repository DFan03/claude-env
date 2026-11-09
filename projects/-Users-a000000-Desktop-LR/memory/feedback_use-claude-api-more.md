---
name: feedback-use-claude-api-more
description: "Route self-contained work to the user's Claude API credit (claude_delegate.py) with model chosen per task; DeepSeek for reading; spare Claude Code balance"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 01d1cb24-0d2f-4c9f-8c0c-d2dca75be215
  modified: 2026-11-09T11:13:24.446Z
---

User advice 2026-11-09: I was using too little Claude API. DeepSeek stays for all paper reading; but use the user's Claude API credit (python3 ~/.claude/tools/claude_delegate.py, budget-guarded, ~$5 of $90 spent) instead of the Claude Code balance (subagents / main session) where the task is self-contained. Pick the better model per task.

**Why:** Claude Code balance is the scarce one; API credit is large and unused. Agent-tool subagents bill the Claude Code balance.

**How to apply:** Opus via API = stats/method review, PI review, adjudicating disagreements; Sonnet via API = new/complex code, drafting; writer_delegate.py for prose; DeepSeek flash/pro for reading. Use Agent-tool subagents only when tools/repo access are needed, and keep the main session lean (delegate, keep conclusions). Always check the [claude_usage] trailer (served == requested) and say so. See [[feedback-close-chrome-tabs]] for the other standing rule.

**DeepSeek tier rule (user 2026-11-09):** both flash and pro are available. Use flash for routine extraction (find a quote, fill a field, list methods, bulk abstract passes); use pro only where judgement or subtle classification matters (is a method linear, adjudication, ambiguous inclusion). Pick per task and say which in briefs; do not default to pro.

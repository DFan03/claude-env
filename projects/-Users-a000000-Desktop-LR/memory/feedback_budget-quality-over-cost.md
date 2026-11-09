---
name: feedback-budget-quality-over-cost
description: User tops up API credit as needed; research quality outranks cost, but no blind or wasteful spend
metadata:
  type: feedback
---

User 2026-11-09: "don't think of budget, I top up once you use up, just make sure you don't waste it blindly, I care the research quality over how much spent."

**Why:** Quality of the review matters more than the bill; the $90 guard in claude_delegate.py is a soft limit they will raise.

**How to apply:** Do not ask for a budget ceiling (D8 resolved) and do not pick weaker models just to save money; use the right model per [[feedback-use-claude-api-more]] (flash routine, pro judgement, Opus/Fable for review). Still dry-run first, report spend after the dry run and at each stage, no unbounded loops, no blind re-runs. If the guard refuses a call, tell the user to top up.

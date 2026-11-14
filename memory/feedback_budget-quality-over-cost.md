---
name: feedback-budget-quality-over-cost
description: Research quality outranks cost; user tops up credit; no blind or wasteful spend
metadata:
  type: feedback
---

User (2026-11-09): "don't think of budget, I top up once you use up, just make sure you don't waste it blindly, I care the research quality over how much spent."

**Why:** review quality matters more than the bill; the guard in claude_delegate.py is a soft limit they will raise.
**How to apply:** don't ask for a budget ceiling and don't pick weaker models just to save money; pick the right model per [[feedback-model-routing]]. Still dry-run first, report spend after the dry run and each stage, no unbounded loops, no blind re-runs. If the guard refuses a call, tell the user to top up.

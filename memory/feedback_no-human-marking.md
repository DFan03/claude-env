---
name: feedback_no-human-marking
description: User will not hand-mark or hand-check items; use an independent strong-model agent instead
metadata:
  type: feedback
---

User (2026-11-10): "I will not mark any grade, for any task like this that you need me to mark something, just use an independent agent with good model."

**Why:** user cannot/does not want to do annotation or agree/disagree sheets.
**How to apply:** replace human confirmation sheets with an independent clean-context Opus/Sonnet+ audit agent that sees source text, not my verdict; report disagreement rate and fixes. State in reports that checks were AI, not human. Fetching paywalled papers is still the user's job ([[feedback_model-routing]]).

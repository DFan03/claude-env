---
name: feedback-advisor-first
description: Consult the clean-context advisor (skill advisor) before asking the user; user is the fallback
metadata:
  type: feedback
---
User (2026-11-10): the master made mistakes below its ability (e.g. struggled to download a PDF while the full text was already on the page). Wants a dedicated Opus/Fable Claude API advisor with clean context as the FIRST place for advice; the user is the fallback.
**Why:** long contexts carry stale assumptions and the master overcomplicates.
**How to apply:** use skill `advisor` when stuck, after 2 failed attempts, before non-trivial plans/workarounds and before escalating a question to the user. Also check what is already in front of me (page text, files) before building a workaround. Related: [[feedback-model-routing]].

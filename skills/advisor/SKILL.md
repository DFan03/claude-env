---
name: advisor
description: First place to seek advice before asking the user. A clean-context Claude API advisor (Opus) that challenges plans, spots overcomplication and simpler routes. Use when stuck, before a non-trivial plan or workaround, after 2 failed attempts, or when a decision looks like it needs the user.
---
# advisor
Rule (user, 2026-11-10): consult the advisor FIRST; the user is the fallback, only if the advisor says the decision is theirs or cannot resolve it.
Write a brief to a file (goal in the user's words, what exists/is available, what was tried, the question, 3-10 key files) then:
```
python3 ~/.claude/tools/claude_delegate.py "Advise on the brief." --model opus --effort high --max-tokens 16000 \
  --system "$(cat ~/.claude/skills/advisor/PERSONA.md)" -c <brief.md> [-c key files] > <project>/handoff/advisor/<n>.md
```
Do not feed it your conclusion as fact; give raw facts and the options. Check `served` in the usage trailer. Report in one line what the advisor said and what you did with it.

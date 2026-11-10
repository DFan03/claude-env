---
name: pi-review
description: Advisory "PI" review of a project's README against the original task, by the best-expert persona (Opus via API). Use before declaring any analysis project finished and after major README changes; apply its edits, then re-run once.
---
# pi-review
The README must answer the ORIGINAL task, in plain language, with biological meaning. This skill has a senior-PI persona review it.

## Run (needs `TASK.md` in the project root = the user's brief verbatim)
```
python3 ~/.claude/tools/claude_delegate.py "Review the project." --model opus --effort high --max-tokens 32000 \
  --system "$(cat ~/.claude/skills/pi-review/PERSONA.md)" -c TASK.md -c README.md [-c results/<key tables>] \
  > changes/<name>/handoff/PI_review.md
```
(API route only: no repo access needed.)

## Then
1. Read the review; apply every item that improves task coverage, plain-language explanation or biology. Do not argue with the PI; if an item is infeasible, say why in the README limitations.
2. Methodology changes the PI proposes go through `sci-spec`/`stat-check`; ask the user before expensive work.
3. Re-run once on the revised README; stop after 2 rounds. Tell the user: verdict line, what changed, what was not done.
4. Check the API call's `[claude_usage]` trailer: `served` must equal the requested model.

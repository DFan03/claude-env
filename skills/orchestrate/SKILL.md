---
name: orchestrate
description: Run a sci-spec tasks.md in parallel across models (DeepSeek flash/pro, Sonnet, Opus) with file-based handoffs. Use when executing an approved change with 2+ independent tasks.
---
# Orchestrate
Routing (default; override in tasks.md):
| Work | Model | How |
|---|---|---|
| Plan, method choice, integration, review | me (master) | direct |
| Critical stats/method review | Opus | API: `claude_delegate.py --model opus --effort high -c <files>` (needs file edits/tools? Agent `scientific-reasoning`) |
| Novel/complex code | Sonnet | API: `claude_delegate.py --model sonnet --standard -c <files>`; I write the returned code to disk |
| Task needing repo exploration / tool use | Sonnet | Agent tool (uses plan quota) |

API workers (`~/.claude/tools/claude_delegate.py`) spend the user's API credit (budget-guarded, ledger at
~/.claude/state/claude_api_ledger.jsonl). Prefer them over Agent-tool subagents for self-contained tasks
(give all needed files via -c). Run several in parallel as background shell jobs. Check `--spent` each wave;
warn the user at 75% of budget.
| Routine code, tests, plots | DeepSeek flash | `deepseek_delegate.py --standard` |
| Paper reading | DeepSeek V4 pro | `paper-digest` skill |

Procedure:
1. Read tasks.md; group tasks into waves by dependency.
2. Per wave, launch all tasks in ONE message (Agent calls) or parallel background shell jobs for DeepSeek. Coding tasks that write files get their own `git worktree` (or distinct file paths) to avoid collisions.
3. Each task prompt = goal + inputs (paths, not contents) + acceptance test + "read ~/.claude/skills/code-standard/PREAMBLE.md" + "write result to changes/<name>/handoff/T<id>.out.md (<=10 lines + paths), return only 'done T<id>'".
4. Downstream tasks receive only the relevant handoff files.
5. After each wave: run pytest, review each output, record accepted/fixed/rejected; fall back to doing it myself if a DeepSeek result fails review (no repeated re-prompts).
6. CLAUDE.md rules still apply: dry run before big runs, ask before cost, CPU-parallel, logs + tail -f.
7. After each wave: update README.md via `living-report` (master only), commit + push.
8. Tell the user one line per wave: "Wave N: k/k tasks passed; README updated; next: ...".

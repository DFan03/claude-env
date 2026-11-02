---
name: orchestrate
description: Run a sci-spec tasks.md in parallel across models (specialist agents) with file-based handoffs. Use when executing an approved change with 2+ independent tasks.
---
# Orchestrate
Routing: see "Specialist agents and model routing" in ~/.claude/CLAUDE.md (owner column of tasks.md = agent name:
reader, coder-light, coder, bioinfo, control-runner, code-reviewer, claim-auditor, repro-auditor, judge, db-lookup, reporter, methods-referee, citation-checker).
Agents cannot spawn agents, so the master launches all independent tasks of a wave in ONE message. Script delegates (`claude_delegate.py`) spend API credit
(budget-guarded, ledger ~/.claude/state/claude_api_ledger.jsonl); check `--spent` each wave, warn at 75%.

Procedure:
1. Read tasks.md; group tasks into waves by dependency.
2. Per wave, launch all tasks in ONE message (Agent calls) or parallel background shell jobs for DeepSeek. Coding tasks that write files get their own `git worktree` (or distinct file paths) to avoid collisions.
3. Each task prompt = goal + inputs (paths, not contents) + acceptance test + "read ~/.claude/skills/code-standard/PREAMBLE.md" + "write result to changes/<name>/handoff/T<id>.out.md (<=10 lines + paths), return only 'done T<id>'".
4. Downstream tasks receive only the relevant handoff files.
5. After each wave: `code-reviewer` + `control-runner` (+ `repro-auditor` at milestones) in parallel -> `judge` filters -> fixer applies; stop after 2 clean rounds or 5. Record accepted/fixed/rejected; if an author agent fails review, do it myself (no repeated re-prompts).
6. CLAUDE.md rules still apply: dry run before big runs, ask before cost, CPU-parallel, logs + tail -f.
7. After each wave: `reporter` updates README.md via `living-report`; `citation-checker`/`claim-auditor` must pass before push.
8. Tell the user one line per wave: "Wave N: k/k tasks passed; README updated; next: ...".

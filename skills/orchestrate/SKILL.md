---
name: orchestrate
description: Run a sci-spec tasks.md in parallel across models (specialist agents) with file-based handoffs. Use when executing an approved change with 2+ independent tasks.
---
# Orchestrate
Routing: see "Specialist agents and model routing" in ~/.claude/CLAUDE.md (owner column of tasks.md = agent name:
reader, coder, bioinfo, control-runner, code-reviewer, claim-auditor, db-lookup, reporter, methods-referee, citation-checker).
Agents cannot spawn agents, so the master launches all independent tasks of a wave in ONE message. Script delegates (`claude_delegate.py`) spend API credit
(budget-guarded, ledger ~/.claude/state/claude_api_ledger.jsonl); check `--spent` each wave, warn at 75%.

Procedure:
1. Read tasks.md; group tasks into waves by dependency.
2. Per wave, launch all tasks in ONE message (Agent calls) or parallel background shell jobs for DeepSeek. Coding tasks that write files get their own `git worktree` (or distinct file paths) to avoid collisions.
3. Each task prompt = goal + inputs (paths, not contents) + acceptance test + "read ~/.claude/skills/code-standard/PREAMBLE.md" + "write result to changes/<name>/handoff/T<id>.out.md (<=10 lines + paths), return only 'done T<id>'".
4. Downstream tasks receive only the relevant handoff files.
5. After each wave: `code-reviewer` (incl. reproducibility checklist) + `control-runner` in parallel -> I filter findings from the handoff files (or one `claude_delegate.py --model best` call) -> fixer applies; stop after 2 clean rounds or 5. Record accepted/fixed/rejected; if an author agent fails review, do it myself (no repeated re-prompts).
6. CLAUDE.md rules still apply: dry run before big runs, ask before cost, CPU-parallel, logs + tail -f.
7. After each wave: `reporter` updates README.md via `living-report`; `citation-checker`/`claim-auditor` must pass before push.
8. Tell the user one line per wave: "Wave N: k/k tasks passed; README updated; next: ...".

## Orchestration rules (added 2026-11-10; patterns adapted from obra/superpowers @22f0b46, own wording)
- **Brief template** (agents start with no context): Goal / Inputs (paths) / Acceptance test / Handoff path / Constraints (budget, files not to touch) / Return format.
- **Status protocol**: every agent's first reply line is DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT, BLOCKED or NEEDS_APPROVAL. Master acts: DONE -> verify; CONCERNS -> read them before use; NEEDS_CONTEXT -> re-brief once; BLOCKED -> change approach or do it myself; NEEDS_APPROVAL -> ask the user.
- **Progress ledger** `changes/<name>/LEDGER.md`: one line per task (id, agent, model, status, handoff path, verified y/n). Update after each wave; it replaces re-reading handoffs.
- **Verification gate**: no task counts as done until its acceptance test was run or its output file opened by me or a reviewer agent; an agent's "done" is a claim, not evidence.
- **Scale effort to task**: a one-file fix is not a wave; use one agent for <=2 small tasks, a wave only for 3+ independent tasks.
- **When not to parallelise**: tasks that write the same files, depend on each other's numbers, or need one shared judgement call.
- **Right worker for the difficulty**: judgement, method, review and interpretation go to the strongest suitable model; cheap models (Haiku, DeepSeek flash) only where output quality is identical (bulk screening, transcription, formatting, schema-checked extraction). Cost never outranks correctness.

## Moved from CLAUDE.md
- Before any code: pre-specified analysis plan (split, metrics, controls, number of variants to try); report ALL variants run. Never tell agents the hoped-for result.
- Review loop: author -> reviewers in parallel -> filter -> fixer; stop after 2 clean rounds or 5. No endless re-prompting.
- Delegate output: always review (accepted / fixed / rejected in the end-of-task summary). Truncation (`output == max_tokens`, empty reply) is a failure; use --max-tokens >= 32000 for reasoning models, report any retry in one line. Check `[claude_usage]` served == requested, keep request_ids.
- Cost: no unbounded loops; flag per-row/per-file batches and ask first.
- Community skills: only after reading the full SKILL.md and scripts; copy into ~/.claude/skills/ pinned to a commit; never run install scripts.

---
name: token-report
description: One-figure token-usage report for a project (tokens by problem type, by API and by model: Claude Code session, Anthropic API delegates, DeepSeek). Use at project milestones/end and whenever the user asks about token use or cost; embed the figure in the project README.
---
# token-report
Builds `figures/token_usage.png` + `results/token_usage.tsv` for the current project and (optionally) its README section.

## Run
`python3 ~/.claude/skills/token-report/token_report.py [--project <root>] [--out figures/token_usage.png]`
(default project = git root of cwd; needs matplotlib, pandas.)

## Sources (all local, no network)
1. Claude Code session transcripts `~/.claude/projects/<encoded root>/**/*.jsonl` -> API "Claude Code session", per model; usage de-duplicated per message id; input = fresh + cache-write, cache reads reported separately.
2. Delegate trailers `[deepseek_usage]` / `[claude_usage]` in tool results -> APIs "DeepSeek" / "Anthropic API (delegate)"; problem type taken from the command that produced them.
3. `~/.claude/state/claude_api_ledger.jsonl` (entries whose cwd is inside the project) -> USD and any call missing a trailer.

## Problem types (heuristic, rule-based; edit RULES in the script to change)
Delegates: Routine code, Complex code, Code review, Method/stats review, Paper reading.
Session turns (by the tools used in the turn): Running analysis, Coding, Testing, Docs/README, Git/reporting, Literature search, Delegation orchestration, Planning & reasoning.

## Rules
- Tell the user the classification is heuristic. Cache-read tokens are shown as a number, not plotted (they dwarf everything and are billed ~10x cheaper).
- After running, embed in README under "Resource use" (`![token usage](figures/token_usage.png)` + 2-line reading) and commit the PNG + TSV.
- DeepSeek has no price table here, so USD covers only the Anthropic API ledger.

## Restart / epoch (added 2026-11-02)
`<project>/.claude/TOKEN_EPOCH` (UTC ISO) makes the report ignore all usage before that time (project restart). `--since` overrides it.
If the work runs in a session launched from a DIFFERENT folder, pass `--transcripts <that root>` (repeatable) so those sessions count.

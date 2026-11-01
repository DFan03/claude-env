---
name: code-standard
description: Coding and testing standard for all agents (Claude, Sonnet, DeepSeek) in scientific Python projects. Use when writing, delegating, or reviewing code so output is consistent.
---
# Code standard
Single source of truth: `~/.claude/skills/code-standard/PREAMBLE.md`.
- Delegating to DeepSeek: `python3 ~/.claude/tools/deepseek_delegate.py "<task>" --standard -c <files>` (injects the preamble).
- Delegating to a Claude subagent: paste the preamble into its prompt (or say "read PREAMBLE.md first").
- Review checklist (me, after every agent output): (1) runs; (2) `pytest -q` passes; (3) matches spec acceptance test; (4) preamble rules followed (seed, logging, no input mutation, no leakage); (5) no secrets. Report as accepted / fixed / rejected.

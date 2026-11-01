---
name: workflow-setup
description: "Multi-model spec-driven workflow set up on 2026-11-01 (skills, DeepSeek model IDs, remote access)"
metadata:
  node_type: memory
  type: project
  originSessionId: f7e1ffcb-0423-40e9-bf51-6b725595b2a5
  modified: 2026-11-01T22:07:01.526Z
---

Skills in ~/.claude/skills: sci-spec, orchestrate, code-standard, paper-digest (+ stat-check). DeepSeek model IDs: `deepseek-flash` (coding), `deepseek-v4-pro` (1M ctx papers); tool aliases flash/pro. Node/npm not installed, so OpenSpec CLI was not used; sci-spec is a native OpenSpec-style skill. User's Max plan includes ~$100 Claude API credit separate from Claude Code: use it via `~/.claude/tools/claude_delegate.py` (Opus/Sonnet workers, budget cap in secrets/anthropic.env, ledger in ~/.claude/state/). ~/.claude is a git repo backed up to private github.com/DFan03/claude-env (whitelist .gitignore, secrets excluded); commit+push after every setup change; restore via bootstrap.sh. Remote access: `/remote-control` (alias /rc) then claude.ai/code or mobile app. See [[user-profile]].

**Why:** efficiency with same quality: expensive models advise, cheap ones code/read.
**How to apply:** follow CLAUDE.md "Workflow" block.

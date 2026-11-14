---
name: reference-claude-env-repo
description: ~/.claude is a git repo backed up to private GitHub; how to restore; API credit and remote access
metadata:
  type: reference
---

~/.claude is a git repo backed up to private github.com/DFan03/claude-env (whitelist .gitignore, secrets excluded). Commit+push after every setup change; restore via ~/.claude/bootstrap.sh. Claude API credit (Max plan, separate from Claude Code) is used via ~/.claude/tools/claude_delegate.py (budget cap in secrets/anthropic.env, ledger in ~/.claude/state/). Remote access: /remote-control (alias /rc), then claude.ai/code or the mobile app.

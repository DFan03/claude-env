#!/usr/bin/env bash
# Restore this Claude Code environment on a new Mac.
#   git clone git@github.com:<you>/claude-env.git ~/.claude   (or into a temp dir and copy over)
#   bash ~/.claude/bootstrap.sh
set -euo pipefail
cd "$HOME/.claude"
mkdir -p secrets state && chmod 700 secrets
python3 -m pip install --user -q anthropic
# Memory dirs are keyed by path (projects/-Users-<name>-<proj>/memory); same username => works as-is.
for pair in "deepseek.env:DEEPSEEK_API_KEY" "anthropic.env:ANTHROPIC_API_KEY"; do
  f="secrets/${pair%%:*}"; var="${pair##*:}"
  if [ ! -s "$f" ]; then
    read -r -s -p "$var (blank to skip): " k; echo
    [ -n "$k" ] && printf '%s=%s\n' "$var" "$k" > "$f" && chmod 600 "$f"
  fi
done
grep -q CLAUDE_API_BUDGET_USD secrets/anthropic.env 2>/dev/null || echo "CLAUDE_API_BUDGET_USD=90" >> secrets/anthropic.env
echo "Done. Re-add plugin marketplaces listed in plugins/known_marketplaces.json via /plugin if missing."

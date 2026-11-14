---
name: reference-ccbox-server
description: Claude Code runs on AWS box "ccbox" with one isolated Linux user per Mac (df, rf); reverse control of the Mac via mac/mac-job/mac-chrome
metadata:
  type: reference
---
- AWS ARM Ubuntu 26.04, 2 vCPU/1.8 GB (+4 GB swap), public 13.53.110.100, tailnet name `ccbox`; admin user `ubuntu` (key ~/Downloads/cc-server.pem), Tailscale SSH on.
- One agent user per Mac: `df` = this work Mac (a000000@donglis-macbook-pro), `rf` = other Mac (created by its mac_setup.sh). Homes 700; separate Claude login, ~/.claude, CLAUDE.md, tmux `main`.
- Mac home sshfs-mounted at the identical path (/Users/a000000); AppArmor override /etc/apparmor.d/local/fusermount3 allows /Users/*/.
- Helpers in ~/bin: mac, mac-job, mac-mount, cc-attach. Mac alias `cc`.
- Web search/browsing runs ON THE SERVER ONLY (WebSearch/WebFetch, then headless `playwright` MCP, user scope of df). Never use Claude in Chrome or a browser on the Mac (user decision 2026-11-14).
- Kit source: ~/ccbox-kit (local git), installed at /opt/ccbox-kit. Related: [[reference-claude-env-repo]].
- Server agents authenticate with a setup-token in ~/.claude/secrets/oauth_token (exported by cc-attach); tmux mouse is off so copy works.

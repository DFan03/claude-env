---
name: reference_ccbox-server
description: Claude Code runs on AWS box "ccbox"; one isolated Linux agent user per Mac (df, rf), Mac reached via sshfs + mac/mac-job
metadata:
  type: reference
---
- Server: AWS ARM Ubuntu 26.04, 2 vCPU/1.8 GB (weak: never compute there). Tailnet 100.124.3.23 (ccbox), public 13.53.110.100.
- Admin: `ssh ccbox-admin` (ubuntu, pem). Kit: ~/ccbox-kit on DF Mac (git), deployed to /opt/ccbox-kit.
- Agents: df = DF Mac (personal, a000000 @100.115.4.2). rf = work Mac: NO Claude/Codex may ever be installed there; human-only setup (~/ccbox-kit/RF_GUIDE.md).
- Isolation: OpenSSH per-Mac key + `from=` IP + AllowUsers user@IP (Tailscale SSH off); nftables per-uid egress (ccbox-firewall, /etc/ccbox/agents):
  own Mac only on tailnet, no ssh elsewhere, no IMDS, no loopback except DNS; hidepid; homes 700; no sudo; tailscaled socket root-only.
- Agent tools: Mac home sshfs-mounted at the same path; `mac <cmd>`, `mac-job <name> <cmd>`; web only on the server (WebSearch/WebFetch, headless Playwright MCP), never Chrome on the Mac.
- Add a Mac: `sudo bash /opt/ccbox-kit/add_mac_user.sh <label> <mac_user> <mac_ip> '<pubkey>'`.
- Location privacy (user, 2026-11-14, strict): no agent may look up or infer where the user is (IP, TZ, locale, Wi-Fi, GPS). Enforced by root-owned /etc/claude-code/{CLAUDE.md,managed-settings.json,no_location_hook.py}; `mac` runs with TZ=UTC; admin only over the tailnet.
- DF Mac pulls server usage logs every 10 min (LaunchAgent com.ccbox.usage-sync, copy in ccbox-kit/mac/) so Mac usage apps (Burnt etc.) work.
- Emergency/full technical reference for any AI: ~/ccbox-kit/SETUP_FOR_AI.md (also /opt/ccbox-kit/ on the server); human guide GUIDE.html / ccbox_Field_Manual.pdf. df holds DFan03 gh login on the server; rf none. Tailscale key expiry disabled for ccbox; AWS public IP not elastic (firewall hardcodes it).

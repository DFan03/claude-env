---
name: reference_git-on-ccbox
description: On ccbox, run git add/commit on the Mac via `mac`; push from the server (gh login as DFan03); server-side commit hangs on sshfs
metadata:
  type: reference
---
Tested 2026-11-14. A server-side `git commit` on the sshfs-mounted repo hung in D state (index scan over sshfs). On the Mac (`mac 'cd ~/Desktop/<repo> && git ...'`) status and commit run fast.
The Mac cannot push over ssh: its credential helper is osxkeychain, locked in a remote session. The server has gh 2.104.0 in ~/bin, logged in as DFan03, with `gh auth setup-git` done, so push from the server: `git -c safe.directory=$PWD push origin main`.
**How to apply:** commit on the Mac, push from the server. If a push says "Everything up-to-date" right after a Mac commit, the sshfs cache is stale: check `git rev-parse HEAD`, then push again. See [[reference_ccbox-server]].

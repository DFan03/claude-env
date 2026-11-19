---
name: reference_mac-clipboard
description: On ccbox, Mac Terminal.app can't get OSC52 copies from tmux; put text on the user's clipboard with `mac pbcopy`
metadata:
  type: reference
---
The user runs Claude Code on ccbox inside tmux and connects from the built-in macOS Terminal.app, which ignores OSC52. Drag-select only lands in the tmux buffer, so the user's ⌘C/⌘V gets nothing.
Working routes (tested 2026-11-14): the user holds Fn while dragging, then ⌘C; or Claude runs `printf '%s' "$TEXT" | mac pbcopy` when asked to "copy X".
**How to apply:** when the user says "copy ...", send the exact text through `mac pbcopy` and confirm with `mac pbpaste`. See [[reference_ccbox-server]].

---
name: feedback-close-chrome-tabs
description: Close Chrome tabs/windows opened via claude-in-chrome as soon as each is finished
metadata:
  node_type: memory
  type: feedback
  originSessionId: 01d1cb24-0d2f-4c9f-8c0c-d2dca75be215
  modified: 2026-11-09T08:28:24.645Z
---

When using claude-in-chrome, close tabs/windows I no longer need (user request, 2026-11-09).

**Why:** ~23 spent tabs from the PDF-download wave piled up; the user had to close them by hand. Closing one tab via tabs_close_mcp collapsed the tab group, after which the tool rejected the other 22 as "not in this session's group", so a batch cleanup at the end does not work.

**How to apply:** close each tab right after its download/read is verified (one close per paper, in the same step), never leave cleanup for the end. Do not close the last tab of a group while more work is queued (the group disappears). If tabs are stranded outside the group, say so and ask the user to close them.

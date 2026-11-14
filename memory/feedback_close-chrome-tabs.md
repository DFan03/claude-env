---
name: feedback-close-chrome-tabs
description: Close each claude-in-chrome tab right after use; end-of-job batch cleanup fails
metadata:
  type: feedback
---

Close Chrome tabs opened via claude-in-chrome as soon as each is finished (user, 2026-11-09).

**Why:** ~23 spent tabs piled up; closing one tab via tabs_close_mcp collapsed the tab group, after which the tool rejected the other 22 as "not in this session's group", so end-of-job cleanup cannot work.
**How to apply:** close each tab in the same step its download/read is verified. Don't close the last tab of a group while more work is queued. If tabs are stranded outside the group, say so and ask the user to close them.

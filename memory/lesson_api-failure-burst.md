---
name: lesson-api-failure-burst
description: Burst of empty/invalid API replies in a bulk run - check credit/auth/rate limit before blaming worker count
metadata:
  type: feedback
---
2026-11-09: a ~160-worker DeepSeek run gave ~40% empty replies from record ~11,000; cause was the account running out of credit, not concurrency (same worker level had run clean).
**Why:** scripts record failures as valid_json=false without crashing, so the log looks fine.
**How to apply:** monitor the invalid/empty rate in the OUTPUT file; at the first burst stop and check balance/auth/rate limit first. See [[feedback-model-routing]].

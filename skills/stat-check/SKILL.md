---
name: stat-check
description: Audit a finished analysis, benchmark, or statistical output for methodological compliance and statistical hygiene. Use when validating results, checking a pipeline run, or before reporting findings. Checks the run against golden standards (reference/golden_standard/ and ~/.claude/standards/) and runs a results-file sanity script.
---

# stat-check

Audit a run against the project's golden standards. Flag problems; don't just report numbers.

## Steps
1. **Gather standards**: read `reference/golden_standard/` (use `SUMMARY.md` files and `checklist.md` if present)
   and `~/.claude/standards/general_principles.md`. If a long source has no `SUMMARY.md`, offer to write one.
2. **List the decisions the run made**: preprocessing, normalization, labeling, splits, tests, thresholds,
   seeds. Take them from the code, configs, and logs, not memory.
3. **Compare each decision to the standards.** Mark each as: follows standard (cite it), deviates (say how),
   or no standard covers it (flag for the user to decide).
4. **Run the hygiene script** on the results file:
   `python3 ~/.claude/skills/stat-check/validate.py results.csv [--p-cols pval --adj-cols padj --expect-seed]`
   Exit code 1 means at least one FAIL. Add `--json` for machine-readable output.
5. **Report in plain language**: a short table (check, status, evidence), then what matters most and what
   to fix. Don't silently fix methodological deviations; ask first.

## Rules
- Never claim a result is valid just because the script passed; it only catches common problems.
- If standards conflict or are silent, ask the user.
- Record the audit outcome in the end-of-task summary (the logging hook picks up the task automatically).

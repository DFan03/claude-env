---
name: living-report
description: Keep each project's GitHub README.md as a living scientific report (status -> final paper-style report). Use after every orchestrate wave, milestone, or new result, and before telling the user results.
---
# Living report (README.md = the project's report)
The user reads results on GitHub first. README.md is the report; chat only points to it.

## Structure (keep this order; sections may be short early on)
1. **Title + one-line status** (bold): current finding or state, date, what's next. Read-only line for a busy reader.
2. **Abstract** (<=6 lines): question, approach, main result with effect size + uncertainty, conclusion.
3. **Background & question**: biological motivation, hypothesis (from changes/*/hypothesis.md), cite [@citekey].
4. **Data**: source, n (independent units), inclusion/exclusion, splits.
5. **Methods**: choice + one-line rationale + standard/paper that justifies it [@citekey]; link to specs/.
6. **Results**: one subsection per question. Each = claim sentence -> figure/table -> n, effect size, CI/uncertainty, test + correction.
7. **Discussion & limitations**: what it means biologically, alternative explanations, what would falsify it.
8. **Next steps** (while in progress) / **Conclusion** (at the end).
9. **Reproducibility**: commands, seeds, env, commit hash of the run.
10. **References**: from reference/literature/library.bib (cited keys only).
11. **Changelog** (collapsed `<details>`): date - what changed in the report.

## Being critical about what to show
- Every figure/table must answer one stated question; if it doesn't, move it to `results/supplementary/` and link it.
- Main text: <= ~5 figures. Prefer the plot that shows the effect + its uncertainty + the baseline (not just the best model's score).
- Show distributions/individual points when n is small; never bar-of-means alone.
- Report negative and null results honestly; don't bury failed approaches (one line + link).
- Numbers in text must match the result files (generate tables from results, don't hand-type).
- Use the `dataviz` skill for figures; save to `figures/` as PNG (+ source script); captions say what, n, and what to notice.
- Run `stat-check` before a result enters the README; mark preliminary results as **(preliminary)**.

## Process
- Master agent owns README.md; workers write handoff files only, never edit README.
- Update after each wave/milestone; commit "report: <what changed>" and push.
- At project end: rewrite as a coherent final report (not a log); move process details to Changelog.

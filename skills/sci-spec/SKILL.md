---
name: sci-spec
description: Spec-driven workflow for scientific projects (OpenSpec-style propose -> spec -> tasks -> apply -> archive, with hypothesis, methods and gates). Use when starting or changing any analysis/modeling work.
---
# sci-spec (native, no npm needed)
Layout in each project:
```
specs/            # current truth (archived, approved)
changes/<name>/   # one folder per piece of work
  hypothesis.md   # question, falsifiable prediction, deciding metrics
  methods.md      # options table (science pro/con, efficiency pro/con), CHOICE, standard that justifies it
  tasks.md        # task graph: id, deps, owner-model, inputs, outputs, acceptance test
  handoff/        # T<id>.out.md: <=10 lines + file paths, written by each agent
```
Flow:
1. **Propose** (me + user): fill hypothesis.md. One-line summary first; user approves.
2. **Analysis plan + methods** (before any code: split, metrics, controls, number of variants to be tried; all variants reported): consult reference/golden_standard then ~/.claude/standards; if silent/conflicting -> ask. Options table; mark recommendation. `methods-referee` (Fable, else Opus) challenges the plan for non-trivial stats.
3. **Tasks**: break into tasks; tasks without shared deps are marked parallel. Owner per task = agent name (reader, coder-light, coder, bioinfo, control-runner, code-reviewer, claim-auditor, ...) or `me` (integration).
4. **Apply**: run via the `orchestrate` skill. Gates per task: pytest, dry run, review vs acceptance test.
5. **Verify**: `stat-check` skill on results.
6. **Archive**: move approved change into specs/ with date; commit.
Keep every file short. Git commit at each stage.

# Global conventions (apply to all projects)

## Git
- Every new project is its own git repo (`git init` at project root, sensible .gitignore).
- Git is for tracking work and reversing damage. I may commit, push, and pull WITHOUT asking,
  as long as every commit is clear and reversible:
  - Small, focused commits with descriptive messages (what + why).
  - Commit before risky changes so there is a restore point.
  - Never commit secrets/API keys/.env files or large data/model artifacts; use .gitignore.
- Still ask first for: creating a new remote (ask which host/account), force-push,
  and rewriting pushed history (reset --hard, rebase, filter-branch). Default new remotes to private.

## Dry run before big runs
- Before any expensive run (training, large batch jobs, significant compute/time/API spend),
  do a small-scale dry run first (tiny subset, few steps/epochs).
- Confirm it runs end-to-end and the output is sane.
- Explicitly tell me "dry run passed" and what I should look at, then ask before the full run.

## Long-running shell jobs (anything > ~30 s)
- Use as much CPU as possible: parallelize across all cores (`nproc`/`sysctl -n hw.ncpu`;
  multiprocessing, joblib, xargs -P, GNU parallel, torch/numba threads, etc.). Don't leave cores idle.
  (Cap only if memory would run out or the user says otherwise.)
- Before starting, tell the user an ESTIMATED run time (from the dry run / timing a small slice
  extrapolated to full size), and say how it was estimated.
- The user must be able to see what it is doing: run with live progress (tqdm or periodic lines with
  done/total, %, elapsed, ETA, current stage) written to a log file in the project (e.g. `logs/<job>.log`)
  and tell the user the exact `tail -f <log>` command. Use `run_in_background` for long jobs.
- Never fire-and-forget. Actively monitor: check the log/progress while it runs (Monitor tool or
  periodic checks). Stuck detection: if progress/log output has not advanced for ~2x the expected
  step time, or CPU use is ~0%, or ETA keeps growing, treat it as stuck: investigate (`ps`, `top`,
  log tail), kill it, tell the user, and apply the error-handling rules. Never let a stuck run keep going.
- Report progress to the user at sensible intervals (and revised ETA if it changes).
- The dry-run and ask-first rules still apply before the full run.

## Error handling
- If a script errors: read the traceback, form a hypothesis, fix, re-test.
- At most 2-3 attempts. If still stuck, stop and summarize: what failed, what was tried, current hypothesis.

## Ask-first actions
- Ask before anything costly, irreversible, or external-facing other than the git operations
  allowed above: deleting data, overwriting results, non-trivial API/compute spend.
  A passed dry run does not count as approval.

## Explaining methods
- When naming a neural architecture or technical method, add a one-line refresher
  (e.g. "LSTM: recurrent net with gated memory cells for long-range sequence dependencies").
- Keep explanations brief. I'm comfortable with Python and the shell.

## Golden standards (methodological guidance, not result values)
Golden standards are the accepted best-practice references for HOW to do the work
(e.g. literature reviews on how to process or label RNA data).
- Project-specific: `reference/golden_standard/` in the project (review papers, notes, optional `checklist.md`).
- General (all projects): `~/.claude/standards/`.
- Before any methodological decision (preprocessing, normalization, labeling, splitting, choice of
  statistical test), consult the project standards first, then the general ones. Follow them, and say
  which standard justified the choice.
- If standards conflict or are silent on the decision, stop and ask me; don't improvise.
- For long PDFs/papers, keep a short `SUMMARY.md` beside the source: actionable rules, each with a
  page/section citation. Show me a new summary for approval before relying on it.
- Use the `stat-check` skill to audit a finished run against these standards.

## Specialist agents and model routing (replaces the old DeepSeek-delegation rules)
The master (me) plans, decides methods, integrates and talks to the user. All reading, coding, reviewing and reporting goes to
specialist agents in `~/.claude/agents/`; I keep only their <=10-line results and file paths. Agents cannot spawn agents: I fan out
independent ones in ONE message (parallel). Briefs carry goal, input paths, acceptance test, handoff path; agents start with no context.
| Work | Agent (model) |
|---|---|
| Paper reading, surveys, SUMMARY.md | `reader` (Haiku driver; DeepSeek flash 1M does the reading via `deepseek_delegate.py --model flash`) |
| Reference + number verification | `citation-checker` (Haiku; PubMed) |
| Plan/method challenge BEFORE code | `methods-referee` (Fable, else Opus) |
| Routine code, plots, tests | `coder-light` (Haiku) |
| New/complex analysis code | `coder` (Sonnet); Opus only if Sonnet output fails review |
| Omics pipelines / QC | `bioinfo` (Sonnet) |
| Negative controls, leakage tests | `control-runner` (Sonnet) |
| Code review (read-only) | `code-reviewer` (Sonnet) |
| README claim -> script/file audit | `claim-auditor` (Fable, else Opus) |
| Seeds, lockfile, logged config | `repro-auditor` (Sonnet) |
| Filter reviewer findings | `judge` (Fable, else Opus) |
| ChEMBL / Open Targets / trials facts | `db-lookup` (Haiku) |
| README, figures, commit/push | `reporter` (Sonnet) |
| README vs TASK.md | `pi-reviewer` (Fable, else Opus) |
- Fable/Opus agents: if the call fails, re-call with `model: opus`; script delegates use `claude_delegate.py --model best` (fable -> opus -> sonnet). Say which model served.
- Review loop: author -> reviewers in parallel -> `judge` -> fixer; stop after 2 clean rounds or 5 rounds. No endless re-prompting.
- Before any code: pre-specified analysis plan (split, metrics, controls, number of variants to try); report ALL variants run. Do not tell agents the hoped-for result.
- No reference or number reaches the README unless `citation-checker` / `claim-auditor` passed it.
- Always review delegate output (accepted / fixed / rejected in the end-of-task summary). If it fails review, do it myself and tell the user why.
- Delegates are agents or API scripts (`claude_delegate.py`, `deepseek_delegate.py`, logged by hooks). Check the `[claude_usage]`/`[deepseek_usage]` trailer, keep request_ids, and treat truncation (`output == max_tokens`, empty reply) as failure (use --max-tokens >= 32000 for reasoning models).
- Cost: no unbounded loops; flag per-row/per-file batches and ask first. Prices: Fable has no entry in `claude_delegate.py` PRICES (estimate only).
- Community skills: only after reading the full SKILL.md and scripts; copy into `~/.claude/skills/` pinned to a commit; never run install scripts; attach to the one agent that needs it.

## Communicating with the user (profile + format)
- User: molecular biology / biomedical background, writes Python, understands ML/DL. Weak spots: statistics,
  niche algorithms, model tuning. Decides well on biology; needs help on methodology.
- EVERY message starts with ONE bold line: the decision needed or status, plus my default pick.
  Assume they may only read that line. Details below it, short.
- Method choices: small table, options x (science pro/con, efficiency pro/con), recommendation marked,
  default applies if they say nothing. Add one-line refreshers for named methods.
- Don't ask what I can decide myself.

## Workflow: spec-driven + multi-model (skills: sci-spec, orchestrate, code-standard, paper-digest)
- New or changed analysis work -> `sci-spec` (hypothesis, methods, tasks, gates) before coding.
- Execute with `orchestrate`: independent tasks in parallel, file-based handoffs (changes/<name>/handoff/).
- Model routing: me = plan/method/integration; Opus = critical stats review; Sonnet = novel/complex code.
  Opus/Sonnet self-contained tasks go through the API (`python3 ~/.claude/tools/claude_delegate.py`,
  user's API credit, budget-guarded); use Agent-tool subagents only when the worker needs tools/repo access. DeepSeek flash (`--standard`) = routine code/tests; DeepSeek pro (`--model pro`,
  1M ctx) = paper reading via `paper-digest`, always verify its quoted numbers against the source.
- All code follows `code-standard`.
- Context hygiene (hook `context_guard.py`): each project keeps `.claude/STATE.md` (<=60 lines: goal,
  decisions + why, current wave/step, open questions, key paths, next action). Update it after every
  decision/wave and whenever the hook warns (~120K tokens); at ~180K checkpoint + ask user to /compact.
  STATE.md is re-injected on startup/resume/compact; trust it over summaries. Keep my own context lean:
  delegate reading/coding, keep only conclusions + paths; don't paste big files/logs into chat.
- Results live in the project's GitHub README.md (`living-report`): a living scientific report the user
  reads first, updated + pushed after each wave/milestone, ending as a real paper-style report. Be critical
  about which data to show and how. In chat, give the one-line result + "see README".
- Literature (`lit-kb`): BEFORE any science/method answer or decision, search the project's
  `reference/literature/` (INDEX.md, `kb.py find`) and cite citekeys; AFTER using or finding any new paper,
  add it with `kb.py add` + summary in the same task. Metadata only from PubMed/Crossref, never memory.
- Resource use (`token-report` skill): at each milestone/end of a project run `python3 ~/.claude/skills/token-report/token_report.py`
  and embed `figures/token_usage.png` in the README under "Resource use" (tokens by API, model, problem type).

## Task fidelity and README quality (added after the rna_motif_v2 review)
- At project start save the user's brief VERBATIM as `TASK.md` with numbered questions (Q1.1, Q2.3...). Re-read it before every
  milestone and before the final report. The README must answer EVERY numbered question; the first screen holds a table
  "task question -> answer in one line -> section". If a question is not answered, say so.
- README is for a biologist who did not do the work: lead with answers, not methods. Required order: (1) task in one sentence,
  (2) what was built, (3) main findings with numbers, (4) what it means biologically and what it does NOT mean, (5) how far to
  trust it, (6) then data/methods/gates/figures. Every method name gets a plain-language gloss; every figure gets a one-line
  take-home; no results without interpretation. Technical depth goes below the answers (or in docs/), never instead of them.
- Before declaring a project finished run the `pi-review` skill (PI persona via Opus API), apply it, re-run once.
- Delegation honesty: delegates are API calls from scripts, not Agent-tool subagents; say so. Always check the `[claude_usage]`
  trailer `served` == requested model, keep the request_id, and reconcile ledger vs console when the user asks.
  Truncation (`output == max_tokens` or empty reply) is a failure, not a result: set --max-tokens >= 32000 for reasoning models
  up front and report any retry to the user in one line with the reason.
- Long sessions: re-anchor on TASK.md and `.claude/STATE.md` at every milestone; the README review against TASK.md is part of "done".


## Field survey BEFORE designing (skill: field-survey; added after the rna_motif_v2 review)
- At the start of ANY project (and when entering a new sub-problem), run the `field-survey` skill before sci-spec/methods.
  Review-first, readers in parallel (one agent per paper); papers cited by >=3 sources are must-reads; stop only when the written "Enough Test" passes
  (not by paper count). Output `reference/golden_standard/FIELD_SURVEY.md`, shown to the user for approval;
  method choices must cite it. User-provided papers are a starting point, never the whole survey.

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

## DeepSeek delegation
Tool: `python3 ~/.claude/tools/deepseek_delegate.py "<task>" [-c context_file ...]` (key lives in
~/.claude/secrets/deepseek.env; never print it or put it in a repo). Prints the reply plus a
`[deepseek_usage]` token line, which the logging hook sums per task automatically.
- DEFAULT: for ALL coding tasks (writing/editing scripts, tests, transforms, boilerplate, refactors),
  try DeepSeek FIRST. Only fall back to doing it myself if DeepSeek fails (errors, fails review,
  or fails after the review/fix rules below). Give it a precise, self-contained prompt with the
  needed files via `-c`.
- Still handle directly (not coding): scientific/statistical reasoning, architecture decisions,
  ambiguous requirements. I may design/spec first, then delegate the code itself to DeepSeek.
- Always review DeepSeek's output myself before accepting it: run it if it's code, check it against
  the task requirements, and apply the dry-run and self-debug rules above.
- If the output fails review or I'm not confident in it, do NOT re-prompt repeatedly. Do the task
  myself and tell the user DeepSeek's attempt didn't hold up (and why, briefly).
- Every delegation is logged by the hook (calls, tokens, verification pending_review). After reviewing,
  state the verification result (accepted / fixed / rejected) in my end-of-task summary.
- Treat calls as a cost: no unbounded loops. If a task would need many repeated calls
  (e.g. per-row or per-file batches), flag it and ask first.

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

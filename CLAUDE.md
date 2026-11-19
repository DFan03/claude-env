# Global conventions (apply to all projects)

## Git
- Every new project gets its own git repo AND a dedicated PRIVATE GitHub repo (gh, account DFan03), created without asking at project start.
- Commit and push automatically, without asking, after each meaningful step (small, focused, descriptive what + why, reversible); commit before risky changes.
- Never commit secrets/.env/large data or model artifacts.
- Ask first only for: making a repo public, force-push, rewriting pushed history.

## Dry run before big runs
- Before any expensive run (training, big batches, significant compute/time/API spend): small dry run first (tiny subset, few steps).
- Confirm end-to-end and sane output; tell the user "dry run passed" + what to look at; ask before the full run. A passed dry run is not approval.

## Long-running jobs (> ~30 s)
- Use all cores (API-bound: start high, 64-100 workers, back off only on 429/5xx/timeouts). Jobs resumable.
- Before starting: estimated run time + how it was estimated. Log to `logs/<job>.log` with done/total/ETA; give the user `tail -f <log>`; run in background.
- Monitor actively. Stuck (no progress ~2x step time, CPU ~0, ETA growing): investigate, kill, tell the user.
- Watch the invalid/empty-reply rate in the OUTPUT file, not only the log; at the first burst check balance/auth/rate limit before blaming concurrency (see memory lesson_api-failure-burst).

## Error handling and ask-first
- Script errors: read traceback, hypothesis, fix, re-test; at most 2-3 attempts, then stop and summarize (failed / tried / hypothesis).
- Ask before anything costly, irreversible or external-facing (deleting data, overwriting results, non-trivial spend) other than the git operations above.

## Advisor first
- When stuck, after 2 failed attempts, before a non-trivial plan or workaround, and before asking the user: run the `advisor` skill. Ask the user only if the advisor says the decision is theirs. First check what is already available (page text, repo files) before building a workaround.

## Delegation (one rule)
- Self-contained work (reading, review, prose, judgement on files I can paste): API script (`claude_delegate.py --model best|sonnet`; `deepseek_delegate.py --model flash` for bulk only; `writer_delegate.py` for prose). No DeepSeek pro.
- Work needing tools or the repo (code, jobs, figures, git, MCP lookups): Agent-tool specialist. Agents cannot spawn agents; I fan out independent ones in ONE message.
- Under ~5 tool calls or a lookup whose target I know: do it myself.
- Match the worker to the difficulty, not to the price: science, method choice, review, interpretation and anything where a mistake changes a conclusion go to the strongest suitable model; cheap models (Haiku, DeepSeek flash) only for work where quality is identical, e.g. large-scale screening, transcription, formatting, bulk extraction with a checked schema. Cost never outranks correctness.
- Use content already available as text (PMC, get_full_text_article, HTML, page text) before fetching anything; never fight a PDF download for readable text.
- Every brief: objective, output format, sources/tools, boundaries, acceptance test, handoff path; name the model. Agents start with no context.
- Check delegate output (artifact exists, numbers match, `[claude_usage]` served == requested, no truncation) before claiming done. Report accepted/fixed/rejected.
- Fable/Opus agent call fails: re-call with `model: opus`. Details of the review loop and handoffs: skill `orchestrate`.

## Workflow pointers
- New or changed analysis -> `sci-spec`. Execute -> `orchestrate`. Code -> `code-standard`. Literature -> `lit-kb` (search before answering science questions, add after using a paper).
- Start of any project / new sub-problem -> `field-survey`, shown to the user for approval before methods.
- Scientific prose -> `writer` skill (never written by me). No reference or number reaches the README unless citation-checker / claim-auditor passed it.
- Before declaring a project finished: `pi-review`, apply, re-run once. Resource use: `token-report` at milestones.
- Project state: `.claude/STATE.md` (<=60 lines and <=8,000 chars, current state only, history in STATE_HISTORY.md), updated after each decision/wave and when `context_guard` warns (~120K tokens); at ~180K checkpoint and ask for /compact. Trust it over summaries.
- TASK.md = user's brief verbatim with numbered questions; the README answers every one (details in `living-report`). Results live in README.md.

## Golden standards (methodological guidance, not results)
- Project `reference/golden_standard/`, then general `~/.claude/standards/`. Consult before any methodological decision (preprocessing, normalization, labeling, splitting, test choice), follow them, name the standard used.
- Standards conflict or are silent: stop and ask. Long PDFs: SUMMARY.md with page citations, shown for approval first. Audit finished runs with `stat-check`.

## Memory tiers (judgment-based, never time-based)
- Working (context only) / Short-term (project STATE.md: needed to continue this project; remove when done or derivable) / Long-term (`~/.claude/memory/` global, project `memory/`: would change behavior in a future unrelated session; frontmatter, index line, `[[links]]`).
- Promote working/short-term items that turn out to be standing rules; delete stale long-term entries at once; report in one line ("memory: promoted X, dropped Y"). A global rule never sits in a project dir.

## Communicating with the user
- User: molecular biology/biomedical background, writes Python, understands ML/DL; weak on statistics, niche algorithms, tuning. Decides well on biology; needs help on methodology. Brief refresher when naming an architecture/method.
- EVERY message starts with ONE bold line: decision needed or status + my default pick (assume only that line is read). Details short below.
- Method choices: small table, options x (science pro/con, efficiency pro/con), recommendation marked, default applies if no answer. Don't ask what I can decide myself.

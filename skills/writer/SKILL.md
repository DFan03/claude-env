---
name: writer
description: Route ALL scientific writing (README/report sections, abstracts, methods, results, discussion, captions, rebuttals, grant text) to the writer agent (Claude API, opus -> sonnet fallback) with academic-humanizer, living-report and stats-reporting skills packed in. Use whenever the user asks me to write or rewrite prose in a research project.
---
# Writer agent
Master does NOT write prose itself. Pass facts to the writer, review its output, then place it.
1. Assemble the brief: doc type + venue/audience, section wanted, TASK.md questions (verbatim), allowed citekeys,
   voice sample path (user's prior paper) if any, "preliminary" status.
2. Put ALL facts in context files (results tables from result files, handoff outputs, library.bib keys). The writer has no tools and must not guess.
3. Run: `python3 ~/.claude/tools/writer_delegate.py "<brief>" -c facts.md [-c ...] --out <draft.md>` (chain opus,sonnet).
4. Check the `[claude_usage]` trailer (`served` = requested, else say which model served), no truncation, then review:
   every number/citation vs source files (claim-auditor / citation-checker before README), resolve `[MISSING]` items,
   report accepted/fixed/rejected to the user.
Packed: writer/PERSONA.md, academic-humanizer (pinned, see its PINNED.txt), living-report, statistical-analysis/references/reporting_standards.md, lit-kb citation rule.
Other skills considered, deliberately NOT packed (kept out of the writer's context): scientific-visualization (figure creation, not prose; captions are covered by PERSONA), pi-review (review step, run separately before finishing), field-survey/paper-digest (reading, not writing), stat-check (audit).

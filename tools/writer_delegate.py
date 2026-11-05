#!/usr/bin/env python3
"""Writer agent: Claude API call (opus, falls back to sonnet) with a packed skill system prompt.

Usage:
  writer_delegate.py "brief text" -c facts.md -c results.csv [--voice reference/voice/VOICE.md] [--out draft.md] [--model opus,sonnet] [--effort high]
  echo "brief" | writer_delegate.py - -c ...
Packed skills (system prompt): writer/PERSONA.md, academic-humanizer/SKILL.md, living-report/SKILL.md,
  statistical-analysis/references/reporting_standards.md (stat reporting wording), lit-kb citation rule.
Brief must hold: document type + target venue/audience, section(s) wanted, voice sample path (optional),
  TASK.md questions (optional), citekeys allowed. Context files hold ALL facts/numbers (writer has no tools).
Delegates to claude_delegate.py (budget guard, ledger, [claude_usage] trailer). Check `served` in the trailer.
"""
import argparse
import subprocess
import sys
from pathlib import Path

H = Path.home() / ".claude"
PACK = [
    ("WRITER PERSONA AND RULES", H / "skills/writer/PERSONA.md"),
    ("SKILL: academic-humanizer", H / "skills/academic-humanizer/SKILL.md"),
    ("SKILL: living-report (structure of README/report)", H / "skills/living-report/SKILL.md"),
    ("REFERENCE: statistical reporting standards", H / "skills/statistical-analysis/references/reporting_standards.md"),
    ("RULE: citations (lit-kb)", None),
]
LITKB = ("Cite only [@citekey]s given in the brief, formatted as in the project library.bib. Never add a reference "
         "or bibliographic detail from memory; if a citation is needed but not supplied, write [MISSING: citation for ...].")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("brief", help="brief text, or '-' for stdin")
    ap.add_argument("-c", "--context-file", action="append", default=[])
    ap.add_argument("--voice", help="VOICE.md style card (skills/voice-merge); packed into the system prompt")
    ap.add_argument("--out", help="also save the writer's reply to this file")
    ap.add_argument("--model", default="opus,sonnet", help="fallback chain, default opus,sonnet")
    ap.add_argument("--effort", default="high", choices=["low", "medium", "high", "xhigh", "max"])
    ap.add_argument("--max-tokens", type=int, default=32000)
    a = ap.parse_args()

    system = "\n\n".join(f"===== {name} =====\n{p.read_text() if p else LITKB}" for name, p in PACK)
    if a.voice:
        system += f"\n\n===== VOICE CARD (imitate structure and register only; never copy wording) =====\n{Path(a.voice).read_text()}"
    cmd = [sys.executable, str(H / "tools/claude_delegate.py"), a.brief if a.brief != "-" else sys.stdin.read(),
           "--model", a.model, "--effort", a.effort, "--max-tokens", str(a.max_tokens), "--system", system]
    for f in a.context_file:
        cmd += ["-c", f]
    r = subprocess.run(cmd, capture_output=True, text=True)
    sys.stderr.write(r.stderr)
    if r.returncode:
        sys.exit(r.stdout + f"\nwriter failed (exit {r.returncode})")
    sys.stdout.write(r.stdout)
    if a.out:
        body = "\n".join(l for l in r.stdout.splitlines() if not l.startswith("[claude_usage]"))
        Path(a.out).write_text(body + "\n")
    if "output truncated" in r.stdout or "[refused" in r.stdout:
        sys.exit("writer output truncated/refused: treat as failure")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Context guard hook: keeps the master agent's context small and recoverable.

Modes (argv[1]):
  prompt   UserPromptSubmit: measure context from the transcript; above thresholds, inject a
           reminder to checkpoint STATE.md (and, higher, to compact).
  pre      PreCompact: snapshot the project's STATE.md + git status before compaction.
  start    SessionStart (startup|resume|compact|clear): inject the project's STATE.md so work
           resumes from the written state, not from a lossy summary.
State file: <project>/.claude/STATE.md (project = git root of cwd, else cwd).
Never blocks: any error -> exit 0 silently.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

WARN, CRIT = 120_000, 180_000  # tokens; degradation starts well below window limits
STATE_NAME = Path(".claude") / "STATE.md"
GLOBAL_MEM = Path.home() / ".claude" / "memory" / "MEMORY.md"
CONSOLIDATE = ("Also consolidate memory by judgment, not by age: long-term (~/.claude/memory or project memory) "
               "= would change my behavior in a future unrelated session; STATE.md = needed to continue this work; "
               "drop what is done, superseded, contradicted, or derivable from the repo.")
MARK_DIR = Path.home() / ".claude" / "state" / "context_guard"


def project_root(cwd: str) -> Path:
    try:
        out = subprocess.run(["git", "-C", cwd, "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, timeout=5)
        if out.returncode == 0:
            return Path(out.stdout.strip())
    except Exception:
        pass
    return Path(cwd)


def context_tokens(transcript: str) -> int:
    last = 0
    with open(transcript, errors="ignore") as f:
        for line in f:
            if '"usage"' not in line:
                continue
            try:
                msg = json.loads(line).get("message")
                u = msg.get("usage") if isinstance(msg, dict) else None
            except Exception:
                continue
            if u:
                last = (u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0)
                        + u.get("cache_creation_input_tokens", 0))
    return last


def emit(event: str, context: str = "", user_msg: str = "") -> None:
    out = {}
    if context:
        out["hookSpecificOutput"] = {"hookEventName": event, "additionalContext": context}
    if user_msg:
        out["systemMessage"] = user_msg
    if out:
        print(json.dumps(out))


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    data = json.load(sys.stdin)
    root = project_root(data.get("cwd") or ".")
    state = root / STATE_NAME

    if mode == "prompt":
        tokens = context_tokens(data["transcript_path"])
        level = 2 if tokens >= CRIT else 1 if tokens >= WARN else 0
        if not level:
            return
        MARK_DIR.mkdir(parents=True, exist_ok=True)
        mark = MARK_DIR / f"{data.get('session_id', 'x')}.level"
        prev = int(mark.read_text()) if mark.exists() else 0
        if level <= prev:  # remind once per level per session
            return
        mark.write_text(str(level))
        k = tokens // 1000
        if level == 1:
            emit("UserPromptSubmit", context=(
                f"[context-guard] Context is ~{k}K tokens (warn {WARN//1000}K). Before continuing: "
                f"update {state} (goal, decisions+why, current step, open questions, key file paths); "
                "offload further reading/coding to subagents/API workers; keep only conclusions here. " + CONSOLIDATE))
        else:
            emit("UserPromptSubmit",
                 context=(f"[context-guard] Context is ~{k}K tokens (critical {CRIT//1000}K). "
                          f"Update {state} NOW, commit it, then tell the user in one line to run /compact "
                          "(STATE.md is re-injected automatically after compaction). " + CONSOLIDATE),
                 user_msg=f"Context ~{k}K tokens: Claude will checkpoint STATE.md; then run /compact.")

    elif mode == "pre":
        if state.exists():
            snap = root / ".claude" / "state_snapshots"
            snap.mkdir(parents=True, exist_ok=True)
            ts = time.strftime("%Y%m%d-%H%M%S")
            git = subprocess.run(["git", "-C", str(root), "status", "--short"],
                                 capture_output=True, text=True, timeout=5).stdout
            (snap / f"STATE-{ts}.md").write_text(state.read_text() + f"\n\n## git status at {ts}\n{git}")
        for m in MARK_DIR.glob(f"{data.get('session_id', 'x')}.level"):
            m.unlink()  # context resets after compaction

    elif mode == "start":
        parts = []
        if GLOBAL_MEM.exists():
            parts.append("[memory] Global long-term memory index (files in ~/.claude/memory/; read one when relevant):\n"
                         + GLOBAL_MEM.read_text()[:4000])
        if state.exists():
            txt = state.read_text()
            if len(txt) > 12000:
                txt = (txt[:8000] + "\n[context-guard] STATE.md is %d chars; middle omitted. Trim it to <=60 lines / 8000 chars NOW.\n" % len(txt) + txt[-3500:])
            parts.append(f"[context-guard] Project state from {state} (source of truth; trust it over any summary):\n"
                         f"{txt}\n[end STATE.md] Follow ~/.claude/CLAUDE.md rules; results go to README.md.")
        if parts:
            emit("SessionStart", context="\n\n".join(parts))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)

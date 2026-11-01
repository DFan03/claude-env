#!/usr/bin/env python3
"""Global workflow logger. Registered in ~/.claude/settings.json for PostToolUse and Stop.

PostToolUse: buffer a compact event in ~/.claude/hooks/state/<session>.jsonl (cheap, silent).
Stop:        condense the buffer into ONE per-task entry and append it to
             <git-root>/.claude/logs/workflow_log.jsonl  (machine-readable)
             <git-root>/.claude/logs/workflow_log.md     (human-readable)
Outside a git repo nothing is written. Never blocks or fails the session.
"""
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

STATE_DIR = Path.home() / ".claude" / "hooks" / "state"
LOGGED_TOOLS = {"Bash", "Edit", "Write", "NotebookEdit"}  # read-only tools are skipped
DELEGATE_MARKERS = ("deepseek_delegate", "mcp__deepseek")


def git_root(cwd):
    try:
        out = subprocess.run(["git", "-C", cwd, "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, timeout=5)
        return Path(out.stdout.strip()) if out.returncode == 0 else None
    except Exception:
        return None


def bash_failed(resp):
    """Best-effort failure detection; tool_response shape varies by version."""
    if isinstance(resp, dict):
        for k in ("exit_code", "exitCode", "returncode"):
            if isinstance(resp.get(k), int):
                return resp[k] != 0
        if resp.get("is_error") or resp.get("interrupted"):
            return True
        text = f"{resp.get('stderr', '')}\n{resp.get('stdout', '')}"
    else:
        text = str(resp)
    return bool(re.search(r"(^|\n)Exit code [1-9]|Traceback \(most recent call last\)", text))


def on_post_tool(data):
    tool = data.get("tool_name", "")
    delegated = any(tool.startswith(m) for m in DELEGATE_MARKERS)
    if tool not in LOGGED_TOOLS and not delegated:
        return
    inp = data.get("tool_input", {}) or {}
    cmd = inp.get("command") or inp.get("file_path") or inp.get("notebook_path") or ""
    if any(m in str(cmd) for m in DELEGATE_MARKERS):
        delegated = True
    out = data.get("tool_response")
    out = out.get("stdout", "") if isinstance(out, dict) else str(out or "")
    um = re.search(r"\[deepseek_usage\] (\{.*?\})", out)
    try:
        usage = json.loads(um.group(1)) if um else None
    except ValueError:
        usage = None
    ev = {
        "usage": usage,
        "tool": tool,
        "target": str(cmd)[:300],
        "desc": inp.get("description", ""),
        "failed": bash_failed(data.get("tool_response")) if tool == "Bash" else False,
        "delegated": delegated,
        "cwd": data.get("cwd", ""),
    }
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with open(STATE_DIR / f"{data.get('session_id', 'x')}.jsonl", "a") as f:
        f.write(json.dumps(ev) + "\n")


def last_user_prompt(transcript_path):
    """Text of the most recent real user message (not a tool result)."""
    try:
        last = ""
        for line in open(transcript_path):
            m = json.loads(line)
            msg = m.get("message", {})
            if m.get("type") != "user" or msg.get("role") != "user":
                continue
            c = msg.get("content")
            if isinstance(c, list):
                c = " ".join(b.get("text", "") for b in c if b.get("type") == "text")
            if isinstance(c, str) and c.strip() and not c.lstrip().startswith("<"):
                last = c.strip()
        return last
    except Exception:
        return ""


def on_stop(data):
    buf = STATE_DIR / f"{data.get('session_id', 'x')}.jsonl"
    if not buf.exists():
        return
    events = [json.loads(l) for l in buf.read_text().splitlines() if l.strip()]
    buf.unlink()  # task consumed regardless of whether we log it
    if not events:
        return
    root = git_root(events[0]["cwd"] or data.get("cwd", "."))
    if root is None:
        return

    task = (last_user_prompt(data.get("transcript_path", "")).splitlines() or ["(unknown task)"])[0][:140]
    bashes = [e for e in events if e["tool"] == "Bash"]
    edits = [e for e in events if e["tool"] != "Bash" and not e["delegated"]]
    files = sorted({Path(e["target"]).name for e in edits})
    delegated = [e for e in events if e["delegated"]]
    commits = [e["target"].split("\n")[0][:100] for e in bashes if re.search(r"\bgit\s+commit\b", e["target"])]

    # Outcome: fail if the LAST bash failed; pending_review if nothing verified the work
    # (edits/delegation with no passing run afterwards); otherwise pass.
    if bashes and bashes[-1]["failed"]:
        outcome = "fail"
    elif delegated or (edits and not any(not b["failed"] for b in bashes)):
        outcome = "pending_review"
    else:
        outcome = "pass"

    tok = {"prompt": 0, "completion": 0, "total": 0}
    for e in delegated:
        for k in tok:
            tok[k] += (e.get("usage") or {}).get(k, 0)

    now = datetime.now().astimezone()
    entry = {
        "timestamp": now.isoformat(timespec="seconds"),
        "session_id": data.get("session_id", ""),
        "task": task,
        "outcome": outcome,
        "n_commands": len(bashes),
        "n_failed_commands": sum(b["failed"] for b in bashes),
        "files_changed": files,
        "commits": commits,
        "delegation": {"used": bool(delegated), "calls": len(delegated),
                       "verification": "pending_review" if delegated else None,
                       "tokens": tok if delegated else None},
        "key_commands": [(b["desc"] or b["target"].split("\n")[0])[:100] for b in bashes[:8]],
    }

    logdir = root / ".claude" / "logs"
    logdir.mkdir(parents=True, exist_ok=True)
    with open(logdir / "workflow_log.jsonl", "a") as f:
        f.write(json.dumps(entry) + "\n")

    md = logdir / "workflow_log.md"
    new = not md.exists()
    with open(md, "a") as f:
        if new:
            f.write("# Workflow log\n\nOne entry per task, appended automatically by ~/.claude/hooks/log_event.py.\n")
        f.write(f"\n## {now:%Y-%m-%d %H:%M} — {task}\n")
        f.write(f"- **Outcome:** {outcome}\n")
        f.write(f"- **Commands:** {len(bashes)} run, {entry['n_failed_commands']} failed\n")
        if files:
            f.write(f"- **Files changed:** {', '.join(files)}\n")
        if commits:
            f.write(f"- **Commits:** {'; '.join(commits)}\n")
        if delegated:
            f.write(f"- **DeepSeek delegation:** {len(delegated)} call(s), verification: pending_review; "
                    f"tokens: {tok['total']} total ({tok['prompt']} in / {tok['completion']} out)\n")
        for c in entry["key_commands"]:
            f.write(f"  - `{c}`\n")


def main():
    try:
        data = json.load(sys.stdin)
        event = data.get("hook_event_name", "")
        if event == "PostToolUse":
            on_post_tool(data)
        elif event == "Stop":
            on_stop(data)
    except Exception:
        pass  # a logging problem must never disrupt the session
    sys.exit(0)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Delegate a simple/mechanical task to DeepSeek (OpenAI-compatible API). Stdlib only.

Usage:
  deepseek_delegate.py "write a pytest for this function" [--context-file f.py ...]
  echo "task text" | deepseek_delegate.py - --context-file data.csv
Key: DEEPSEEK_API_KEY from env, else ~/.claude/secrets/deepseek.env.
Output: model reply on stdout, then one trailer line:
  [deepseek_usage] {"model":..., "prompt":N, "completion":N, "total":N}
The workflow-log hook parses that trailer to record token use per task.
Always review the output yourself before using it.
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

URL = "https://api.deepseek.com/chat/completions"
ENV_FILE = Path.home() / ".claude" / "secrets" / "deepseek.env"
SYSTEM = ("You are a careful assistant doing a small, well-specified mechanical task "
          "(boilerplate, tests, formatting, simple transforms). Output only what was asked: "
          "no preamble. For code, output a single code block unless told otherwise. "
          "If the task is ambiguous, say what is unclear instead of guessing.")


def load_key():
    if os.environ.get("DEEPSEEK_API_KEY"):
        return os.environ["DEEPSEEK_API_KEY"]
    try:
        for line in ENV_FILE.read_text().splitlines():
            if line.startswith("DEEPSEEK_API_KEY="):
                return line.split("=", 1)[1].strip().strip("'\"")
    except OSError:
        pass
    sys.exit(f"error: DEEPSEEK_API_KEY not set and not found in {ENV_FILE}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("task", help="task description, or '-' to read from stdin")
    ap.add_argument("--context-file", "-c", action="append", default=[],
                    help="file whose contents are included as context (repeatable)")
    ap.add_argument("--model", default="deepseek-flash",
                    help="deepseek-flash (coding, default) | deepseek-v4-pro (1M ctx: paper reading); aliases: flash, pro")
    ap.add_argument("--standard", action="store_true",
                    help="prepend ~/.claude/skills/code-standard/PREAMBLE.md to the system prompt")
    ap.add_argument("--system", default=SYSTEM)
    ap.add_argument("--temperature", type=float, default=0.0)
    ap.add_argument("--max-tokens", type=int, default=None, help="optional output cap (default: none)")
    ap.add_argument("--timeout", type=int, default=180)
    a = ap.parse_args()

    a.model = {"flash": "deepseek-flash", "pro": "deepseek-v4-pro"}.get(a.model, a.model)
    if a.standard:
        a.system = (Path.home() / ".claude/skills/code-standard/PREAMBLE.md").read_text() + "\n\n" + a.system
    task = sys.stdin.read() if a.task == "-" else a.task
    parts = [task.strip()]
    for f in a.context_file:
        parts.append(f"\n--- context: {f} ---\n{Path(f).read_text()}")
    body = {"model": a.model, "temperature": a.temperature, "stream": False,
            "messages": [{"role": "system", "content": a.system},
                         {"role": "user", "content": "\n".join(parts)}]}
    if a.max_tokens:
        body["max_tokens"] = a.max_tokens

    req = urllib.request.Request(URL, json.dumps(body).encode(), {
        "Content-Type": "application/json", "Authorization": f"Bearer {load_key()}"})
    try:
        with urllib.request.urlopen(req, timeout=a.timeout) as r:
            resp = json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"error: DeepSeek HTTP {e.code}: {e.read().decode()[:500]}")
    except Exception as e:
        sys.exit(f"error: DeepSeek call failed: {e}")

    print(resp["choices"][0]["message"]["content"])
    u = resp.get("usage", {})
    usage = {"model": a.model, "prompt": u.get("prompt_tokens", 0),
             "completion": u.get("completion_tokens", 0), "total": u.get("total_tokens", 0)}
    print(f"[deepseek_usage] {json.dumps(usage)}")


if __name__ == "__main__":
    main()

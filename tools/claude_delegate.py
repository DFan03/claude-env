#!/usr/bin/env python3
"""Delegate a task to Claude via the Anthropic API (uses API credit, not the Claude Code plan).

Usage:
  claude_delegate.py "task" [-c file ...] [--model sonnet|opus|haiku] [--effort low|medium|high]
                     [--standard] [--system TEXT] [--max-tokens N]
  echo "task" | claude_delegate.py - -c data.py
  claude_delegate.py --spent            # show total spend vs budget
Key:    ANTHROPIC_API_KEY in ~/.claude/secrets/anthropic.env (never exported to the shell).
Budget: CLAUDE_API_BUDGET_USD in the same file (default 90). Calls are refused once spend >= budget.
Ledger: ~/.claude/state/claude_api_ledger.jsonl (one JSON line per call, with estimated USD).
Output: reply on stdout, then a trailer line:
  [claude_usage] {"model":..., "input":N, "output":N, "usd":X, "spent_total":Y, "budget":Z}
Parallel use: run several instances as background shell jobs; the ledger is lock-protected.
"""
import argparse
import fcntl
import json
import sys
import time
from pathlib import Path

import anthropic

HOME = Path.home() / ".claude"
ENV_FILE = HOME / "secrets" / "anthropic.env"
LEDGER = HOME / "state" / "claude_api_ledger.jsonl"
PREAMBLE = HOME / "skills" / "code-standard" / "PREAMBLE.md"
MODELS = {"opus": "claude-opus-5-5", "sonnet": "claude-sonnet-5-5", "haiku": "claude-haiku-5-5"}
# USD per 1M tokens: (input, output, cache_read). Source: claude-api skill table, cached 2026-10-06.
PRICES = {"claude-opus-5-5": (4.0, 20.0, 0.20), "claude-sonnet-5-5": (2.0, 10.0, 0.20),
          "claude-haiku-5-5": (0.10, 0.50, 0.01)}
SYSTEM = ("You are a careful expert assistant doing a well-specified task for a scientific project. "
          "Output only what was asked, no preamble. For code, output complete files in code blocks. "
          "If the task is ambiguous or underspecified, say what is unclear instead of guessing.")


def load_env() -> dict:
    env = {}
    try:
        for line in ENV_FILE.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip("'\"")
    except OSError:
        pass
    if not env.get("ANTHROPIC_API_KEY"):
        sys.exit(f"error: ANTHROPIC_API_KEY not found in {ENV_FILE}")
    return env


def spent_total() -> float:
    if not LEDGER.exists():
        return 0.0
    return sum(json.loads(l).get("usd", 0.0) for l in LEDGER.read_text().splitlines() if l.strip())


def record(entry: dict) -> float:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    with open(LEDGER, "a+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.write(json.dumps(entry) + "\n")
        f.flush()
        fcntl.flock(f, fcntl.LOCK_UN)
    return spent_total()


def cost(model: str, u) -> float:
    pin, pout, pcache = PRICES.get(model, (4.0, 20.0, 0.20))
    cache_read = getattr(u, "cache_read_input_tokens", 0) or 0
    return (u.input_tokens * pin + u.output_tokens * pout + cache_read * pcache) / 1e6


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("task", nargs="?", help="task text, or '-' for stdin")
    ap.add_argument("--context-file", "-c", action="append", default=[])
    ap.add_argument("--model", default="sonnet", help="sonnet (default) | opus | haiku | full model id")
    ap.add_argument("--effort", choices=["low", "medium", "high", "xhigh", "max"], default="high")
    ap.add_argument("--standard", action="store_true", help="prepend code-standard PREAMBLE.md")
    ap.add_argument("--system", default=SYSTEM)
    ap.add_argument("--max-tokens", type=int, default=64000)
    ap.add_argument("--spent", action="store_true", help="print spend vs budget and exit")
    a = ap.parse_args()

    env = load_env()
    budget = float(env.get("CLAUDE_API_BUDGET_USD", 90))
    total = spent_total()
    if a.spent:
        print(f"spent ${total:.2f} of ${budget:.2f} budget")
        return
    if not a.task:
        ap.error("task is required")
    if total >= budget:
        sys.exit(f"error: API budget reached (${total:.2f} >= ${budget:.2f}); ask the user")

    model = MODELS.get(a.model, a.model)
    system = (PREAMBLE.read_text() + "\n\n" + a.system) if a.standard else a.system
    parts = [(sys.stdin.read() if a.task == "-" else a.task).strip()]
    for f in a.context_file:
        parts.append(f"\n--- context: {f} ---\n{Path(f).read_text()}")

    client = anthropic.Anthropic(api_key=env["ANTHROPIC_API_KEY"], max_retries=3)
    t0 = time.time()
    try:
        with client.messages.stream(
            model=model, max_tokens=a.max_tokens, system=system,
            output_config={"effort": a.effort},
            messages=[{"role": "user", "content": "\n".join(parts)}],
        ) as stream:
            msg = stream.get_final_message()
    except anthropic.AuthenticationError:
        sys.exit("error: invalid Anthropic API key")
    except anthropic.NotFoundError as e:
        sys.exit(f"error: model/endpoint not found: {e.message}")
    except anthropic.RateLimitError:
        sys.exit("error: rate limited; retry later")
    except anthropic.APIStatusError as e:
        sys.exit(f"error: API {e.status_code}: {e.message}")
    except anthropic.APIConnectionError:
        sys.exit("error: network error")

    if msg.stop_reason == "refusal":
        print("[refused by safety classifier: escalate to master agent]")
    print("".join(b.text for b in msg.content if b.type == "text"))
    if msg.stop_reason == "max_tokens":
        print("[warning: output truncated at max_tokens]")
    usd = cost(model, msg.usage)
    total = record({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "model": model, "effort": a.effort,
                    "input": msg.usage.input_tokens, "output": msg.usage.output_tokens,
                    "usd": round(usd, 5), "secs": round(time.time() - t0, 1), "cwd": str(Path.cwd())})
    print("[claude_usage] " + json.dumps({"model": model, "input": msg.usage.input_tokens,
          "output": msg.usage.output_tokens, "usd": round(usd, 4),
          "spent_total": round(total, 2), "budget": budget}))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""One-figure token-usage report: by problem type, API and model. See SKILL.md."""
from __future__ import annotations
import argparse, collections, json, re, subprocess
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HOME = Path.home() / ".claude"
API_COLOR = {"Claude Code session": "#2a78d6", "Anthropic API (delegate)": "#eb6834", "DeepSeek": "#1baf7a"}
TRAILER = re.compile(r"\[(deepseek|claude)_usage\] (\{.*?\})")
# session-turn rules: first match wins (priority order); matched against tool names + command/path text
SESSION_RULES = [
    ("Literature search", r"WebSearch|WebFetch|mcp__.*(pubmed|biorxiv|consensus)|kb\.py"),
    ("Delegation orchestration", r"deepseek_delegate|claude_delegate"),
    ("Testing", r"pytest"),
    ("Git/reporting", r"\bgit (commit|push|add)|living-report|README"),
    ("Running analysis", r"python3? .*\.py|\bnode |Rscript"),
    ("Docs/README", r"(Edit|Write)\b.*\.(md|bib|txt)\b"),
    ("Coding", r"\bEdit\b|\bWrite\b"),
]
DEFAULT_SESSION = "Planning & reasoning"
MODELS_SHORT = lambda m: m.replace("claude-", "").replace("-5-5", " 5.5").replace("deepseek-", "DS ")

def delegate_type(cmd: str, api: str, model: str) -> str:
    c = cmd.lower()
    if api == "DeepSeek":
        return "Paper reading" if re.search(r"\.pdf|digest|--model pro|paper", c) else "Routine code"
    if "opus" in model: return "Method/stats review"
    if "review" in c: return "Code review"
    return "Complex code"

def session_type(blob: str) -> str:
    for name, pat in SESSION_RULES:
        if re.search(pat, blob): return name
    return DEFAULT_SESSION

def project_root(arg: str | None) -> Path:
    if arg: return Path(arg).resolve()
    r = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    return Path(r.stdout.strip() if r.returncode == 0 else ".").resolve()

def collect(root: Path, since: str = "", transcripts: list[str] | None = None) -> pd.DataFrame:
    """since = UTC ISO timestamp: ignore anything earlier (project restart). transcripts = extra project roots whose sessions count."""
    from datetime import datetime, timezone
    epoch = datetime.fromisoformat(since.replace("Z", "+00:00")) if since else None
    if epoch is not None and epoch.tzinfo is None: epoch = epoch.replace(tzinfo=timezone.utc)
    files = []
    for r in [str(root)] + list(transcripts or []):
        files += sorted((HOME / "projects" / re.sub(r"[^A-Za-z0-9]", "-", r)).glob("**/*.jsonl"))
    msgs: dict[str, dict] = {}          # message id -> usage/tools
    uses: dict[str, tuple[str, str]] = {}   # tool_use_id -> (name, text)
    rows: list[dict] = []
    for f in files:
        for line in f.open():
            try: m = json.loads(line)
            except ValueError: continue
            if epoch is not None and m.get("timestamp"):
                if datetime.fromisoformat(m["timestamp"].replace("Z", "+00:00")) < epoch: continue
            msg = m.get("message") or {}
            content = msg.get("content")
            if m.get("type") == "assistant" and isinstance(msg, dict) and msg.get("usage"):
                mid = msg.get("id") or m.get("uuid"); u = msg["usage"]; model = msg.get("model", "")
                if not model or model.startswith("<"): continue
                e = msgs.setdefault(mid, {"model": model, "blob": ""})
                e.update(inp=u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0),
                         cread=u.get("cache_read_input_tokens", 0), out=u.get("output_tokens", 0))
                for b in content if isinstance(content, list) else []:
                    if b.get("type") == "tool_use":
                        i = b.get("input", {}); txt = " ".join(str(i.get(k, "")) for k in ("command", "file_path", "query", "url"))
                        uses[b["id"]] = (b["name"], txt); e["blob"] += f" {b['name']} {txt}"
            elif m.get("type") == "user" and isinstance(content, list):
                for b in content:
                    if b.get("type") != "tool_result": continue
                    out = b.get("content"); out = " ".join(x.get("text", "") for x in out) if isinstance(out, list) else str(out or "")
                    src_cmd = uses.get(b.get("tool_use_id"), ("", ""))[1]
                    if not re.search(r"delegate|digest", src_cmd): continue   # ignore trailers merely echoed (cat/grep of old outputs)
                    for kind, js in TRAILER.findall(out):
                        try: u = json.loads(js)
                        except ValueError: continue
                        cmd = uses.get(b.get("tool_use_id"), ("", ""))[1]
                        api = "DeepSeek" if kind == "deepseek" else "Anthropic API (delegate)"
                        inp = u.get("prompt", u.get("input", 0)); outt = u.get("completion", u.get("output", 0))
                        rows.append({"api": api, "model": u.get("model", ""), "problem": delegate_type(cmd, api, u.get("model", "")),
                                     "input": inp, "cache_read": 0, "output": outt, "usd": u.get("usd", 0.0), "calls": 1})
    for e in msgs.values():
        rows.append({"api": "Claude Code session", "model": e["model"], "problem": session_type(e["blob"]),
                     "input": e.get("inp", 0), "cache_read": e.get("cread", 0), "output": e.get("out", 0), "usd": 0.0, "calls": 1})
    # ledger entries inside the project that no transcript trailer accounts for
    seen = collections.Counter((r["model"], r["input"], r["output"]) for r in rows if r["api"] == "Anthropic API (delegate)")
    led = HOME / "state" / "claude_api_ledger.jsonl"
    if led.exists():
        for line in led.open():
            try: d = json.loads(line)
            except ValueError: continue
            if not str(d.get("cwd", "")).startswith(str(root)): continue
            if epoch is not None and datetime.fromisoformat(d["ts"]).astimezone(timezone.utc) < epoch: continue
            k = (d["model"], d["input"], d["output"])
            if seen[k] > 0: seen[k] -= 1; continue
            rows.append({"api": "Anthropic API (delegate)", "model": d["model"], "problem": "Unclassified delegate",
                         "input": d["input"], "cache_read": 0, "output": d["output"], "usd": d.get("usd", 0), "calls": 1})
    # attach ledger USD to trailer rows (trailers carry usd for Claude delegates already)
    return pd.DataFrame(rows)

def plot(df: pd.DataFrame, out: Path, title: str) -> None:
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
    ink, mute, grid = "#0b0b0b", "#52514e", "#e4e3df"
    fig = plt.figure(figsize=(13, 6.2), facecolor="#fcfcfb")
    gs = fig.add_gridspec(1, 3, width_ratios=[1.15, 1, 1], wspace=0.55, left=0.2, right=0.985, top=0.80, bottom=0.12)
    # A: per api/model, input vs output (log)
    g = df.groupby(["api", "model"])[["input", "output"]].sum().reset_index()
    g["tot"] = g.input + g.output; g = g.sort_values("tot")
    ax = fig.add_subplot(gs[0]); y = range(len(g))
    for i, (_, r) in enumerate(g.iterrows()):
        c = API_COLOR[r.api]
        ax.barh(i + 0.19, max(r.input, 1), 0.34, color=c, label=None)
        ax.barh(i - 0.19, max(r.output, 1), 0.34, color=c, alpha=0.45)
        ax.text(max(r.input, 1) * 1.15, i + 0.19, f"{int(r.input):,}", va="center", fontsize=7.5, color=mute)
        ax.text(max(r.output, 1) * 1.15, i - 0.19, f"{int(r.output):,}", va="center", fontsize=7.5, color=mute)
    ax.set_yticks(list(y)); ax.set_yticklabels([f"{MODELS_SHORT(m)}\n{a}" for a, m in zip(g.api, g.model)], fontsize=8)
    ax.set_xscale("log"); ax.set_xlim(1, g.tot.max() * 12); ax.set_title("A  By API and model (solid = input, light = output)", loc="left", fontsize=9.5, color=ink)
    ax.xaxis.grid(True, color=grid); ax.set_axisbelow(True); ax.set_xlabel("tokens (log scale)", color=mute)
    # B/C: per problem type, stacked by api
    p = df.groupby(["problem", "api"])[["input", "output"]].sum().unstack(fill_value=0)
    order = (p["input"].sum(axis=1) + p["output"].sum(axis=1)).sort_values().index
    for k, (col, lab) in enumerate((("input", "B  Input tokens by problem type"), ("output", "C  Output tokens by problem type"))):
        ax = fig.add_subplot(gs[1 + k]); left = pd.Series(0.0, index=order)
        for api in API_COLOR:
            if api not in p[col].columns: continue
            v = p[col][api].reindex(order).fillna(0)
            ax.barh(range(len(order)), v, left=left, color=API_COLOR[api], edgecolor="#fcfcfb", linewidth=1.5, label=api); left += v
        for i, t in enumerate(left): ax.text(t + left.max() * 0.015, i, f"{int(t):,}", va="center", fontsize=7.5, color=mute)
        ax.set_yticks(range(len(order))); ax.set_yticklabels(order if k == 0 else [], fontsize=8)
        ax.set_xlim(0, left.max() * 1.25); ax.set_title(lab, loc="left", fontsize=9.5, color=ink)
        ax.xaxis.grid(True, color=grid); ax.set_axisbelow(True); ax.set_xlabel("tokens", color=mute)
        ax.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, _: f"{x/1000:.0f}k" if x else "0"))
    h = [plt.Rectangle((0, 0), 1, 1, color=c) for c in API_COLOR.values()]
    fig.legend(h, list(API_COLOR), loc="upper right", ncol=3, frameon=False, bbox_to_anchor=(0.985, 0.955), fontsize=9)
    tot_in, tot_out, cr = int(df.input.sum()), int(df.output.sum()), int(df.cache_read.sum())
    n_by = df.groupby("api").calls.sum().to_dict(); usd = df.usd.sum()
    fig.text(0.02, 0.955, f"Token usage: {title}", fontsize=13, fontweight="bold", color=ink, va="top")
    fig.text(0.02, 0.905, f"Input {tot_in:,}  |  output {tot_out:,}  |  cache-read {cr:,} (not plotted)  |  calls/turns: "
             + ", ".join(f"{k} {v}" for k, v in n_by.items()) + f"  |  Anthropic-API spend ${usd:.2f}", fontsize=8.5, color=mute, va="top")
    fig.text(0.02, 0.025, "Input = fresh + cache-write tokens. Problem type is rule-based (see token_report.py). DeepSeek has no price table, so USD covers the Anthropic API only.",
             fontsize=7.5, color=mute)
    out.parent.mkdir(parents=True, exist_ok=True); fig.savefig(out, dpi=170, facecolor=fig.get_facecolor()); plt.close(fig)

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--project"); ap.add_argument("--out", default="figures/token_usage.png"); ap.add_argument("--tsv", default="results/token_usage.tsv")
    ap.add_argument("--since", default=""); ap.add_argument("--transcripts", action="append", default=[])
    a = ap.parse_args(); root = project_root(a.project)
    ef = root / ".claude" / "TOKEN_EPOCH"
    since = a.since or (ef.read_text().strip() if ef.exists() else "")
    df = collect(root, since, a.transcripts)
    if df.empty: raise SystemExit(f"no usage found for {root}")
    out = Path(a.out) if Path(a.out).is_absolute() else root / a.out; tsv = Path(a.tsv) if Path(a.tsv).is_absolute() else root / a.tsv
    tsv.parent.mkdir(parents=True, exist_ok=True)
    df.groupby(["api", "model", "problem"], as_index=False)[["input", "cache_read", "output", "usd", "calls"]].sum().to_csv(tsv, sep="\t", index=False)
    plot(df, out, root.name); print(f"wrote {out} and {tsv}")
    print(df.groupby(["api", "problem"])[["input", "output", "calls"]].sum().to_string())

if __name__ == "__main__":
    main()

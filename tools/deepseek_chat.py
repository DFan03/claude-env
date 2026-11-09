#!/usr/bin/env python3
"""Interactive chat with DeepSeek in YOUR terminal (stdlib only). Key from ~/.claude/secrets/deepseek.env (never printed).
Run:  python3 ~/.claude/tools/deepseek_chat.py [--model flash|pro] [--system "role text"] [--system-file f]
Commands: /file <path>  add a file's text to the conversation | /save <path>  save last reply | /model flash|pro | /usage | /reset | /quit
Transcript: ~/.claude/state/deepseek_chat_<timestamp>.md.  Streams replies. Default model flash (cheap); pro only if you ask."""
import argparse, json, os, sys, time, urllib.request
from pathlib import Path
URL = "https://api.deepseek.com/chat/completions"
def key():
    k = os.environ.get("DEEPSEEK_API_KEY")
    if k: return k
    for l in (Path.home() / ".claude/secrets/deepseek.env").read_text().splitlines():
        if l.startswith("DEEPSEEK_API_KEY"): return l.split("=", 1)[1].strip().strip("'\"")
    sys.exit("no DeepSeek key")
M = {"flash": "deepseek-flash", "pro": "deepseek-v4-pro"}
ap = argparse.ArgumentParser(); ap.add_argument("--model", default="flash"); ap.add_argument("--system", default=""); ap.add_argument("--system-file")
a = ap.parse_args(); model = M.get(a.model, a.model); K = key()
sysm = Path(a.system_file).read_text() if a.system_file else a.system
msgs = [{"role": "system", "content": sysm}] if sysm else []
log = Path.home() / f".claude/state/deepseek_chat_{time.strftime('%Y%m%d_%H%M%S')}.md"; log.parent.mkdir(exist_ok=True)
tot = {"p": 0, "c": 0}; last = ""
print(f"DeepSeek chat ({model}). /quit to exit. Transcript: {log}")
while True:
    try: u = input("\nyou> ").strip()
    except (EOFError, KeyboardInterrupt): break
    if not u: continue
    if u == "/quit": break
    if u == "/reset": msgs = msgs[:1] if sysm else []; print("reset"); continue
    if u == "/usage": print(tot); continue
    if u.startswith("/model"): model = M.get(u.split()[-1], u.split()[-1]); print("model:", model); continue
    if u.startswith("/save"): Path(u.split(maxsplit=1)[1]).write_text(last); print("saved"); continue
    if u.startswith("/file"):
        p = Path(u.split(maxsplit=1)[1]).expanduser(); u = f"[file {p.name}]\n" + p.read_text(errors="ignore")[:400000]
        print(f"(added {len(u)} chars; now ask your question)"); msgs.append({"role": "user", "content": u}); continue
    msgs.append({"role": "user", "content": u})
    req = urllib.request.Request(URL, json.dumps({"model": model, "messages": msgs, "stream": True, "stream_options": {"include_usage": True}}).encode(),
                                 {"Authorization": "Bearer " + K, "Content-Type": "application/json"})
    out = ""; print("deepseek> ", end="", flush=True)
    try:
        for line in urllib.request.urlopen(req, timeout=600):
            line = line.decode().strip()
            if not line.startswith("data:") or line.endswith("[DONE]"): continue
            d = json.loads(line[5:])
            if d.get("usage"): tot["p"] += d["usage"].get("prompt_tokens", 0); tot["c"] += d["usage"].get("completion_tokens", 0)
            for ch in d.get("choices", []):
                t = (ch.get("delta") or {}).get("content") or ""; out += t; print(t, end="", flush=True)
    except Exception as e: print(f"\n[error: {str(e)[:200]}]"); msgs.pop(); continue
    print(); msgs.append({"role": "assistant", "content": out}); last = out
    with open(log, "a") as f: f.write(f"## you\n{u[:3000]}\n\n## {model}\n{out}\n\n")

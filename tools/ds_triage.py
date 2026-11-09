#!/usr/bin/env python3
import json, os, re, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
LIT="/Users/a000000/rna_motif_v3/reference/literature"
QF="/Users/a000000/rna_motif_v3/reference/golden_standard/SURVEY_QUESTIONS.md"
DEL=str(Path.home()/".claude/tools/deepseek_delegate.py")
TOK=[0]; CH=[0]
def loadq(p):
    q=[]
    for l in Path(p).read_text(errors="replace").splitlines():
        m=re.match(r"(Q-[^\s:]+)\s*:?\s*(.*)$",l[2:].strip()) if l.startswith("- Q-") else None
        if m: q.append((m.group(1),m.group(2).strip()))
    return q
def cited(ck,d,own):
    m=re.match(r"([A-Za-z]+)[-_]?(\d{4})",ck)
    sur,yr=(m.group(1).lower(),m.group(2)) if m else (None,None)
    must=[]; other=[]
    for p in sorted(Path(d,"papers").glob("*.md")):
        if p.name==own: continue
        inm=False
        for l in p.read_text(errors="replace").splitlines():
            s=l.strip(); low=s.lower()
            if not s: continue
            if re.search(r"must[- ]reads?",low) and (s.startswith("#") or len(s)<80): inm=True; continue
            if s.startswith("#"): inm=False
            hit=ck.lower() in low or (sur is not None and sur in low and yr in low)
            if hit: (must if inm else other).append(s[:300])
    out=[]
    for x in must+other:
        if x not in out: out.append(x)
        if len(out)>=3: break
    return out
def abstract(pm,txt):
    try:
        L=Path(txt).read_text(errors="replace").splitlines()
        if len(L)>1: return "\n".join(L[2:])[:2500]
    except Exception: pass
    u="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&rettype=abstract&retmode=text&id="+pm
    for _ in range(3):
        try:
            with urllib.request.urlopen(u,timeout=30) as r: return r.read().decode("utf-8","replace")
        except Exception: time.sleep(2)
    raise RuntimeError("efetch failed")
def llm(prompt,ctx):
    fd,tmp=tempfile.mkstemp(); os.close(fd); Path(tmp).write_text(ctx); CH[0]+=len(prompt)+len(ctx)
    try: r=subprocess.run(["python3",DEL,prompt,"-c",tmp,"--model","flash","--max-tokens","8000","--timeout","600"],capture_output=True,text=True,timeout=660)
    finally: os.unlink(tmp)
    if r.returncode: raise RuntimeError((r.stderr or "delegate failed")[-200:])
    out=[]
    for l in r.stdout.splitlines():
        if l.startswith("[deepseek_usage]"):
            try: TOK[0]+=int(json.loads(l.split("]",1)[1]).get("total",0) or 0)
            except Exception: pass
        else: out.append(l)
    return "\n".join(out)
def sections(text):
    L=text.splitlines()[2:]; h=[]
    for i,l in enumerate(L):
        s=l.strip()
        if not s or len(s)>=90 or s.endswith("."): continue
        nxt=next((L[j].strip() for j in range(i+1,len(L)) if L[j].strip()),"")
        if len(nxt)>len(s): h.append(i)
    return [(L[i].strip(),"\n".join(L[i+1:(h[k+1] if k+1<len(h) else len(L))]).strip()) for k,i in enumerate(h)]
def choose(secs,qids,qmap):
    qt=" ".join(qmap[q].lower() for q in qids); qw=set(re.findall(r"[a-z0-9]+",qt)); sc=[]
    for i,(t,b) in enumerate(secs):
        tl=t.lower(); s=len(set(re.findall(r"[a-z0-9]+",tl))&qw)
        if re.search(r"result|discussion|conclusion|abstract|finding",tl): s+=5
        if re.search(r"introduction|background|reference",tl): s-=6
        if "method" in tl:
            if re.search(r"measure|quantif|validat|half-life|dataset|null|control",qt): s+=1
            else: s-=10
        if s>0: sc.append((s,i,t,b))
    if not sc: return []
    sc.sort(key=lambda x:(-x[0],x[1])); out=[]; tot=0
    for s,i,t,b in sc:
        n=len(t)+len(b)+8
        if out and tot+n>30000: continue
        out.append((i,t,b)); tot+=n
        if tot>=30000: break
    out.sort(); return out
def block(out,q):
    m=re.search(r"^###\s+"+re.escape(q)+r"\b.*$",out,re.M)
    if not m: return None
    r=out[m.end():]; n=re.search(r"^#{2,3}\s+",r,re.M); return out[m.start():m.end()+(n.start() if n else len(r))].rstrip()
def nf_ids(out,qs):
    r=[]
    for q in qs:
        b=block(out,q); first=[x.strip() for x in b.splitlines()[1:] if x.strip()] if b else []
        if not first or first[0].lower().strip(".:")=="not found": r.append(q)
    return r
def replace_block(out,q,new):
    old=block(out,q)
    return out.rstrip()+"\n\n"+new.strip() if old is None else out.replace(old,new.strip(),1)
def note(p,status,body):
    p=Path(p)
    if p.exists() and 'status: read' in p.read_text(errors='replace')[:400] and not os.environ.get('FORCE'): p=p.with_suffix('.triage.md')
    lines=p.read_text(errors="replace").splitlines() if p.exists() else []
    end=next((i for i in range(1,len(lines)) if lines[i].strip()=="---"),None) if lines and lines[0].strip()=="---" else None
    fm=lines[:end+1] if end is not None else ["---","---"]
    hit=False
    for i,x in enumerate(fm):
        if re.match(r"^status:",x): fm[i]="status: "+status; hit=True
    if not hit: fm.insert(len(fm)-1,"status: "+status)
    p.parent.mkdir(parents=True,exist_ok=True); p.write_text("\n".join(fm)+"\n"+body.rstrip()+"\n")
def log(lit,ck,stage,nq,secs):
    d=Path(lit).resolve().parent.parent/"logs"/"triage"; d.mkdir(parents=True,exist_ok=True)
    with open(d/"triage_log.tsv","a") as f: f.write(f"{ck}\t{stage}\t{nq}\t{CH[0]}\t{TOK[0]}\t{secs:.1f}\n")
def run(ck,pm,lit,qf,must):
    t0=time.time(); qs=loadq(qf); qmap=dict(qs); np_=Path(lit,"papers",ck+".md"); txt=Path(lit,"txt",ck+".txt")
    cf=cited(ck,lit,ck+".md"); ab=abstract(pm,str(txt) if txt.exists() else None)
    p1='Triage this paper. Reply JSON only: {"relevant":bool,"qids":[...],"reason":str,"abstract_sufficient":bool}. qids from the list the paper can plausibly answer. No prose.'
    c1="ABSTRACT:\n"+ab+"\n\nCITED FOR:\n"+"\n".join(cf or ["(none)"])+"\n\nQUESTIONS:\n"+"\n".join(f"- {q}: {t}" for q,t in qs)
    raw=llm(p1,c1); k=raw.find("{")
    if k<0: raise ValueError("no JSON in triage reply")
    j=json.JSONDecoder().raw_decode(raw[k:])[0]; qids=[q for q in j.get("qids",[]) if q in qmap]
    if not j.get("relevant") or not qids:
        r=str(j.get("reason",""))[:300]; note(np_,"skipped","skipped\nreason: "+r+"\ncited_for: "+("; ".join(cf) or "(none)"))
        log(lit,ck,"B1-skip",0,time.time()-t0); print(f"SKIP {ck} {r} {TOK[0]}"); return 0
    qtext="\n".join(f"- {q}: {qmap[q]}" for q in qids); chosen=[]
    if txt.exists() and not j.get("abstract_sufficient"):
        chosen=choose(sections(txt.read_text(errors="replace")),qids,qmap)
        if not chosen:
            note(np_,"skipped","skipped\nreason: no relevant section\ncited_for: "+("; ".join(cf) or "(none)"))
            log(lit,ck,"B2-stop",len(qids),time.time()-t0); print("STOP-NOSECTION"); return 0
    pctx="\n\n".join(f"## {t}\n{b}" for _,t,b in chosen) if chosen else ab
    p3=("Read the excerpts and answer ONLY these ids. Report THIS paper's own findings; statements about other work in an Introduction are not findings (label them background or skip).  Markdown only. For each: '### Q-id', 'Answer:' (<=4 lines), 'Quote:' (exact quote for every number; none if no number), 'Section:'. If unanswered output exactly '### Q-id' then 'not found'. "
        "Then '## Not stated / caveats' (cell type, m1psi/modification, IVT vs endogenous, readout, tumour/oncolytic, n, statistics; or not stated). Then '## Must-reads it points to' (only works printed in text). Never invent numbers.")
    out=llm(p3,"QUESTIONS:\n"+qtext+"\n\nTEXT:\n"+pctx); stage="B3"
    nf=nf_ids(out,qids)
    if must and nf and txt.exists():
        p4="Answer ONLY these not-found ids from the full text. Markdown only: '### Q-id', 'Answer:' (<=4 lines), 'Quote:' (exact for every number), 'Section:'; or exactly '### Q-id' then 'not found'. Then '## Not stated / caveats'. Never invent numbers."
        o4=llm(p4,"QUESTIONS:\n"+"\n".join(f"- {q}: {qmap[q]}" for q in nf)+"\n\nFULL TEXT:\n"+txt.read_text(errors="replace")[:200000])
        for q in nf:
            b=block(o4,q)
            if b: out=replace_block(out,q,b)
        nf=nf_ids(out,qids); stage="B4"
    tags=["[cited-for]"]+(["[sections: "+", ".join(t for _,t,_ in chosen)+"]"] if chosen else ["[abstract]"])+(["[full-text]"] if stage=="B4" else [])
    body="## Cited for\n"+("\n".join("- "+x for x in cf) if cf else "- (none)")+"\n\n"+out.strip()+"\n\n_Reader: DeepSeek flash, targeted "+" ".join(tags)+"._"
    note(np_,"read",body); log(lit,ck,stage,len(qids),time.time()-t0)
    print(f"OK {ck} {stage} {','.join(qids)} {TOK[0]}"); return 0
def main():
    ck=sys.argv[1] if len(sys.argv)>1 else "?"
    try:
        pm=sys.argv[2]; lit=LIT; qf=QF; must=False; i=3
        while i<len(sys.argv):
            a=sys.argv[i]
            if a=="--lit": lit=sys.argv[i+1]; i+=2
            elif a=="--qfile": qf=sys.argv[i+1]; i+=2
            else: must=must or a=="--must"; i+=1
        return run(ck,pm,lit,qf,must)
    except Exception as e: print(f"FAIL {ck} {str(e)[:200]}"); return 1
if __name__=="__main__": sys.exit(main())

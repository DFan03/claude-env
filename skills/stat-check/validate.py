#!/usr/bin/env python3
"""Generic statistical-hygiene checks on a results table (CSV or JSON list of records). Stdlib only.

Usage: validate.py results.csv [--p-cols a,b] [--adj-cols c] [--expect-seed] [--json]
Exit code 1 if any check FAILs; WARNs don't change the exit code.
"""
import argparse
import csv
import json
import math
import re
import sys

P_RE = re.compile(r"^(p|pval|pvalue|p_value|p-value|raw_p)$", re.I)
ADJ_RE = re.compile(r"^(padj|p_adj|adj_p|adj_pval|fdr|qval|q_value|q|p_adjusted|bonferroni)$", re.I)
SCORE_RE = re.compile(r"(accuracy|acc|auc|auroc|f1|r2|r_squared|precision|recall)", re.I)


def load(path):
    if path.endswith(".json"):
        rows = json.load(open(path))
        if isinstance(rows, dict):
            rows = [rows]
    else:
        rows = list(csv.DictReader(open(path, newline="")))
    return rows


def num(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--p-cols", default="", help="comma list of raw p-value columns (auto-detected if omitted)")
    ap.add_argument("--adj-cols", default="", help="comma list of adjusted p-value columns")
    ap.add_argument("--expect-seed", action="store_true", help="warn if no seed column/key is present")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    rows = load(a.path)
    out = []  # (check, status, evidence)
    add = lambda c, s, e: out.append((c, s, e))
    if not rows:
        add("non-empty", "FAIL", "no rows found")
        return finish(out, a)
    cols = list(rows[0].keys())
    add("non-empty", "PASS", f"{len(rows)} rows, {len(cols)} columns")

    # NaN / inf / missing in numeric-looking columns
    bad = {}
    for c in cols:
        for r in rows:
            raw = r.get(c)
            v = num(raw)
            if raw in ("", None) or (v is not None and (math.isnan(v) or math.isinf(v))):
                bad[c] = bad.get(c, 0) + 1
    add("missing/NaN/inf", "WARN" if bad else "PASS",
        ", ".join(f"{c}: {n}" for c, n in bad.items()) if bad else "none")

    # duplicate rows
    seen, dups = set(), 0
    for r in rows:
        k = tuple(str(r.get(c)) for c in cols)
        dups += k in seen
        seen.add(k)
    add("duplicate rows", "WARN" if dups else "PASS", f"{dups} duplicates")

    # constant numeric columns
    const = []
    for c in cols:
        vals = [num(r.get(c)) for r in rows]
        if all(v is not None for v in vals) and len(rows) > 2 and len(set(vals)) == 1:
            const.append(c)
    add("constant columns", "WARN" if const else "PASS", ", ".join(const) or "none")

    # p-values
    pcols = [c for c in a.p_cols.split(",") if c] or [c for c in cols if P_RE.match(c)]
    acols = [c for c in a.adj_cols.split(",") if c] or [c for c in cols if ADJ_RE.match(c)]
    for c in pcols + acols:
        vals = [v for v in (num(r.get(c)) for r in rows) if v is not None and not math.isnan(v)]
        out_of_range = sum(not (0 <= v <= 1) for v in vals)
        add(f"{c} in [0,1]", "FAIL" if out_of_range else "PASS", f"{out_of_range} out of range of {len(vals)}")
    for c in pcols:
        vals = [v for v in (num(r.get(c)) for r in rows) if v is not None and 0 <= v <= 1]
        if len(vals) >= 20:
            if not acols:
                add("multiple-testing correction", "WARN",
                    f"{len(vals)} raw p-values in '{c}' but no adjusted column (padj/FDR/q). Correct and state the method.")
            low = sum(v < 0.05 for v in vals) / len(vals)
            if low > 0.5:
                add(f"{c} fraction < 0.05", "WARN", f"{low:.0%} significant: check for leakage, batch effects, or a miscalibrated test")
            zeros = sum(v == 0 for v in vals)
            if zeros:
                add(f"{c} exact zeros", "WARN", f"{zeros} p-values are exactly 0 (underflow? report as < smallest float)")
            hist = [0] * 10
            for v in vals:
                hist[min(int(v * 10), 9)] += 1
            add(f"{c} histogram (10 bins)", "PASS", " ".join(map(str, hist)) +
                "  (null-heavy data is ~flat; a spike near 0 plus flat tail is typical of real signal)")

    # too-perfect scores (possible leakage)
    for c in cols:
        if SCORE_RE.search(c):
            vals = [v for v in (num(r.get(c)) for r in rows) if v is not None]
            if vals and min(vals) >= 0.999:
                add(f"{c} too perfect", "WARN", f"all values >= 0.999 (min {min(vals):.4f}): suspect leakage")

    # sample size / replicate info
    if not any(re.search(r"(^n$|n_|_n$|samples|replicate|count)", c, re.I) for c in cols):
        add("sample size reported", "WARN", "no n / samples / replicates column found; report n alongside results")

    # seed
    if a.expect_seed and not any("seed" in c.lower() for c in cols):
        add("seed recorded", "WARN", "no seed column; record random seed with results")

    finish(out, a)


def finish(out, a):
    if a.json:
        print(json.dumps([{"check": c, "status": s, "evidence": e} for c, s, e in out], indent=2))
    else:
        w = max(len(c) for c, _, _ in out)
        for c, s, e in out:
            print(f"{s:<5} {c:<{w}}  {e}")
        n = {k: sum(s == k for _, s, _ in out) for k in ("PASS", "WARN", "FAIL")}
        print(f"\nSummary: {n['PASS']} pass, {n['WARN']} warn, {n['FAIL']} fail")
    sys.exit(1 if any(s == "FAIL" for _, s, _ in out) else 0)


if __name__ == "__main__":
    main()

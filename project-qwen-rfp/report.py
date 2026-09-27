#!/usr/bin/env python3
"""Summarise and compare runs.

    ./.venv/bin/python report.py                 # per-model summary table
    ./.venv/bin/python report.py --compare       # where models disagree, per field
    ./.venv/bin/python report.py --flags         # every unverified/no-quote answer
    ./.venv/bin/python report.py --doc AB-2025   # one document, all models

Disagreement is the useful signal before ground truth exists. Fields where every
model says the same thing are cheap to verify and unlikely to discriminate between
models; fields where they diverge are where the benchmark's answer actually lives,
and where annotation effort is worth spending first.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

from rfpbench.fields import FIELDS

ROOT = Path(__file__).parent


def load(out_dir: Path) -> dict:
    """{backend: {doc_id: record}}"""
    runs = defaultdict(dict)
    for path in sorted(out_dir.rglob("*.json")):
        rec = json.loads(path.read_text())
        runs[path.parent.name][rec["doc_id"]] = rec
    return runs


def norm(answer: dict) -> str:
    """A comparable rendering of one answer, for agreement checks."""
    if not answer or not answer.get("present"):
        return "<absent>"
    v = answer.get("value")
    if v is None and answer.get("email") is not None:
        v = answer.get("email") or answer.get("name")
    if isinstance(v, list):
        parts = []
        for item in v:
            if isinstance(item, dict):
                parts.append(str(item.get("category") or item.get("coverage_type") or item))
            else:
                parts.append(str(item))
        v = " | ".join(sorted(p.strip().lower() for p in parts))
    return " ".join(str(v).split()).lower()[:120]


def summary(runs: dict) -> None:
    print(f"{'backend':22s} {'docs':>5s} {'present':>8s} {'absent':>7s} "
          f"{'grounded':>9s} {'halluc':>7s} {'err':>4s} {'cost$':>8s} {'sec/doc':>8s}")
    print("-" * 88)
    for backend, docs in sorted(runs.items()):
        n = len(docs)
        pres = sum(r["summary"]["fields_asserted_present"] for r in docs.values())
        absent = sum(r["summary"]["fields_absent"] for r in docs.values())
        g = [r["summary"]["groundedness"] for r in docs.values()
             if r["summary"]["groundedness"] is not None]
        h = [r["summary"]["hallucination_rate"] for r in docs.values()
             if r["summary"]["hallucination_rate"] is not None]
        cost = sum(r["totals"]["cost_usd"] for r in docs.values())
        lat = sum(r["totals"]["latency_s"] for r in docs.values())
        err = sum(r["totals"]["errors"] for r in docs.values())
        print(f"{backend:22s} {n:5d} {pres:8d} {absent:7d} "
              f"{(sum(g)/len(g) if g else 0):9.3f} {(sum(h)/len(h) if h else 0):7.3f} "
              f"{err:4d} {cost:8.3f} {lat/n if n else 0:8.1f}")


def compare(runs: dict, doc_filter: str | None) -> None:
    backends = sorted(runs)
    if len(backends) < 2:
        print("need at least two backends to compare")
        return
    docs = sorted({d for b in backends for d in runs[b]})
    agree = disagree = 0

    for doc_id in docs:
        if doc_filter and doc_filter.lower() not in doc_id.lower():
            continue
        present = [b for b in backends if doc_id in runs[b]]
        if len(present) < 2:
            continue
        header_done = False
        for spec in FIELDS:
            vals = {b: norm(runs[b][doc_id]["fields"].get(spec.key)) for b in present}
            if len(set(vals.values())) == 1:
                agree += 1
                continue
            disagree += 1
            if not header_done:
                print(f"\n=== {doc_id[:70]} ===")
                header_done = True
            print(f"  {spec.key}")
            for b in present:
                ans = runs[b][doc_id]["fields"].get(spec.key) or {}
                ev = (ans.get("_evidence") or {}).get("status", "-")
                print(f"     {b:20s} [{ev:10s}] {vals[b][:90]}")

    total = agree + disagree
    if total:
        print(f"\nfield-level agreement: {agree}/{total} = {100*agree/total:.1f}%"
              f"   ({disagree} disagreements -> annotate these first)")


def flags(runs: dict) -> None:
    """Answers whose evidence did not check out. Each is either a real fabrication
    or a bug in the checker - both are worth looking at before trusting a number."""
    n = 0
    for backend, docs in sorted(runs.items()):
        for doc_id, rec in sorted(docs.items()):
            for key, ans in rec["fields"].items():
                st = (ans.get("_evidence") or {}).get("status")
                if st in ("unverified", "no_quote"):
                    n += 1
                    print(f"\n[{backend}] {doc_id[:56]}\n  field={key}  status={st}  "
                          f"score={(ans.get('_evidence') or {}).get('best_score')}")
                    print(f"  value: {str(ans.get('value'))[:140]}")
                    print(f"  quote: {str(ans.get('quote'))[:200]}")
    print(f"\n{n} flagged answers" if n else "\nno flagged answers")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=str(ROOT / "results"))
    ap.add_argument("--compare", action="store_true")
    ap.add_argument("--flags", action="store_true")
    ap.add_argument("--doc", help="substring filter on document id")
    args = ap.parse_args()

    runs = load(Path(args.out))
    if not runs:
        print("no results yet")
        return 1

    if args.flags:
        flags(runs)
    elif args.compare:
        compare(runs, args.doc)
    else:
        summary(runs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

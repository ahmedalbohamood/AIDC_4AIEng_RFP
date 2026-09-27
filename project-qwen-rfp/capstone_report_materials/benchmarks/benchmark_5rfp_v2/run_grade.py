#!/usr/bin/env python3
"""Grade the isolated 5-RFP V2 Lift benchmark.

Reuses grade.py's grade_field()/BY_KEY unmodified (imported, not copied/edited)
against only benchmark_5rfp_v2/ground_truth and benchmark_5rfp_v2/results -
never touches the project's main results/ or ground_truth/ directories.
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent.parent
BENCH = Path(__file__).parent
sys.path.insert(0, str(ROOT))

import grade as G  # noqa: E402  (project's existing grading logic, unmodified)
from rfpbench.fields import BY_KEY, FIELDS  # noqa: E402

FIELD_ORDER = [f.key for f in FIELDS]

ap = argparse.ArgumentParser()
ap.add_argument("--backend", default="lift-vision", help="results subdir under benchmark_5rfp_v2/results/")
ap.add_argument("--out", default=None, help="output json path (default: grading_output_<backend>.json)")
args = ap.parse_args()
BACKEND = args.backend
OUT_PATH = Path(args.out) if args.out else BENCH / f"grading_output_{BACKEND}.json"

gt_files = sorted((BENCH / "ground_truth").glob("*.json"))
assert len(gt_files) == 5, f"expected 5 GT files, got {len(gt_files)}"

per_doc = {}
per_field = defaultdict(lambda: defaultdict(int))
by_difficulty = defaultdict(lambda: defaultdict(int))
overall = defaultdict(int)
diagnostics = []          # partial/wrong/missing rows
grader_mismatches = []    # possible grader mismatch flags
evidence_counts = defaultdict(int)

for gt_file in gt_files:
    gt = json.loads(gt_file.read_text())
    doc_id = gt["doc_id"]
    result_file = BENCH / "results" / BACKEND / f"{doc_id}.json"
    if not result_file.exists():
        print(f"[MISSING RESULT] {doc_id}", file=sys.stderr)
        continue
    record = json.loads(result_file.read_text())
    fields = record["fields"]

    doc_tally = defaultdict(int)
    for key in FIELD_ORDER:
        truth = gt["fields"][key]
        spec = BY_KEY[key]
        diff = truth.get("difficulty", "medium")
        answer = fields.get(key)
        verdict, why = G.grade_field(spec, truth, answer)

        overall[verdict] += 1
        doc_tally[verdict] += 1
        per_field[key][verdict] += 1
        by_difficulty[diff][verdict] += 1

        # evidence / groundedness bookkeeping (only meaningful when GT says present)
        if truth.get("present"):
            if answer is None:
                evidence_counts["missing_answer"] += 1
            else:
                status = (answer.get("_evidence") or {}).get("status", "n/a")
                evidence_counts[f"present_gt::{status}"] += 1
        else:
            if answer is not None and answer.get("present"):
                evidence_counts["absent_gt_but_asserted_present"] += 1
            else:
                evidence_counts["absent_gt_correctly_absent"] += 1

        if verdict != "correct":
            diagnostics.append({
                "document": doc_id,
                "field": key,
                "difficulty": diff,
                "ground_truth_present": truth.get("present"),
                "ground_truth_value": truth.get("value"),
                "lift_present": (answer or {}).get("present"),
                "lift_value": (answer or {}).get("value"),
                "grade": verdict,
                "why": why,
            })

        # crude "possible grader mismatch" heuristic: partial/wrong verdicts where
        # judge note signals high similarity/recall, worth a human's second look
        if verdict in ("partial", "wrong") and answer is not None:
            if ("similarity=" in why and any(f"similarity={n}" in why for n in
                    [str(x) for x in range(60, 100)])) or "coverage=8" in why or "coverage=9" in why:
                grader_mismatches.append({
                    "document": doc_id, "field": key, "grade": verdict, "why": why,
                })

    total_doc = sum(doc_tally.values())
    per_doc[doc_id] = {
        "correct": doc_tally["correct"], "partial": doc_tally["partial"],
        "wrong": doc_tally["wrong"], "missing": doc_tally["missing"],
        "total": total_doc,
        "accuracy": round(doc_tally["correct"] / total_doc, 4) if total_doc else 0,
        "latency_s": record["totals"]["latency_s"],
        "prompt_tokens": record["totals"]["prompt_tokens"],
        "completion_tokens": record["totals"]["completion_tokens"],
        "n_pages": record["n_pages"],
    }

total_all = sum(overall.values())
assert total_all == 85, f"expected 85 graded fields, got {total_all}"

result = {
    "overall": dict(overall),
    "total": total_all,
    "accuracy": round(overall["correct"] / total_all, 4),
    "adjusted_accuracy": round((overall["correct"] + 0.5 * overall["partial"]) / total_all, 4),
    "per_document": per_doc,
    "per_field": {k: dict(v) for k, v in per_field.items()},
    "by_difficulty": {k: dict(v) for k, v in by_difficulty.items()},
    "evidence_counts": dict(evidence_counts),
    "diagnostics": diagnostics,
    "grader_mismatches": grader_mismatches,
    "latency": {
        "per_doc_s": {d: v["latency_s"] for d, v in per_doc.items()},
        "total_s": round(sum(v["latency_s"] for v in per_doc.values()), 2),
        "mean_s": round(statistics.mean(v["latency_s"] for v in per_doc.values()), 2),
        "median_s": round(statistics.median(v["latency_s"] for v in per_doc.values()), 2),
    },
    "tokens": {
        "prompt_tokens_total": sum(v["prompt_tokens"] for v in per_doc.values()),
        "completion_tokens_total": sum(v["completion_tokens"] for v in per_doc.values()),
    },
}
result["tokens"]["total_tokens"] = (result["tokens"]["prompt_tokens_total"] +
                                     result["tokens"]["completion_tokens_total"])
result["tokens"]["avg_total_per_rfp"] = round(result["tokens"]["total_tokens"] / 5, 1)
result["tokens"]["avg_prompt_per_rfp"] = round(result["tokens"]["prompt_tokens_total"] / 5, 1)
result["tokens"]["avg_completion_per_rfp"] = round(result["tokens"]["completion_tokens_total"] / 5, 1)

OUT_PATH.write_text(json.dumps(result, indent=2, ensure_ascii=False))
print(f"wrote {OUT_PATH}")
print(json.dumps({k: result[k] for k in ("overall", "total", "accuracy", "adjusted_accuracy")}, indent=2))

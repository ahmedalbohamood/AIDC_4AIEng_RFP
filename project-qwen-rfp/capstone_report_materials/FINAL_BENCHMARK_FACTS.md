# Final Benchmark Facts

Built entirely from existing, already-computed benchmark outputs
(`benchmark_5rfp_v2/benchmark_summary*.json`, `grading_output*.json`, and the
prior live-inspection evidence file `RFP_CAPSTONE_EVIDENCE.md`, dated 2026-09-22).
**No benchmark or grading run was re-executed to produce this file.**

Grading definitions, formulas, and the exact code path are in `BENCHMARK_METHOD.md`.

---

## SECTION A — the final, identical 5-RFP V2 benchmark

Ground truth: `ground_truth/ground_truth_5_rfps_combined_V2.json`
(sha256 `a26cd8378b680ea60555f59429c5c9750a449dd192b89c3ce78677d66868c03d`).
Documents: the 5 PDFs in `rfps/` / `RFP_FILES.txt`, identical across every model
in this section. **These are the only runs directly comparable to each other.**

| Model | Docs | Fields | Correct | Partial | Wrong | Missing | Accuracy | Adjusted Accuracy | Groundedness | Halluc. Rate | Avg Latency (s) | Prompt Tok | Completion Tok | Total Tok |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **Lift** (`datalab-to/lift`, vision) | 5/5 | 85 | 36 | 38 | 9 | 2 | 42.4% | 64.7% | 0.87 | 0.13 | 168.17 | 874,213 | 22,978 | 897,191 |
| **Qwen3.5-9B** (`QuantTrio/Qwen3.5-9B-AWQ`, text) | 5/5 | 85 | 42 | 30 | 13 | 0 | 49.4% | 67.1% | 0.887 | 0.113 | 59.17 | 241,863 | 17,043 | 258,906 |
| **Qwen3-VL-32B** (`QuantTrio/Qwen3-VL-32B-Instruct-AWQ`, vision) | **2/5 — INCOMPLETE** | n/a | n/a | n/a | n/a | n/a | **NOT GRADED** | **NOT GRADED** | n/a | n/a | n/a | n/a | n/a | n/a |
| GPT / OpenAI | **0/5 — NOT RUN** | — | — | — | — | — | **MISSING** | — | — | — | — | — | — | — |
| K2-Horizon | **0/5 — NOT RUN** | — | — | — | — | — | **MISSING** | — | — | — | — | — | — | — |
| Llama-70B | **0/5 — NOT RUN** | — | — | — | — | — | **MISSING** | — | — | — | — | — | — | — |

**Qwen3-VL-32B on this benchmark: only 2 of the 5 documents were ever extracted**
(`benchmark_5rfp_v2/results_qwen_large_tmp/qwen3-vl-32b-vision/` contains exactly 2
result files; the extraction log, `logs/qwen_large_extraction_run.log`, shows
extraction was in progress — 540s and 304s per document — when it stopped;
`code/run_grade_benchmark5rfp_v2.py`'s own assertion (`assert len(gt_files) == 5`)
means it can only score a complete 5-doc run, so no `grading_output` or
`benchmark_summary` JSON exists for this backend at all). **Do not report a
Qwen3-VL-32B accuracy number for this benchmark — it does not exist.**

GPT-4o, K2-Horizon-7B, and Llama-3.3-70B have **never been run** against this
specific 5-document / V2-ground-truth combination — their results in Section B
below come from a different, larger, non-identical 11-document corpus and are
**not comparable** to the numbers above.

**Do not declare a winner from Section A.** Only Lift and Qwen3.5-9B have
complete, graded, identical-condition runs, and both were single runs (no
repeated trials / confidence intervals) — treat the 7-point accuracy gap as
directional, not a proven ranking.

### Per-field comparison — Lift vs. Qwen3.5-9B (only two models with complete graded results on the identical 5-doc set)

Values are `{verdict: count}` out of 5 documents per field, from
`grading_output.json` / `grading_output_qwen35_9b.json`.

| # | Field | Lift | Qwen3.5-9B |
|---|---|---|---|
| 1 | submission_deadline | correct:1 partial:4 | correct:1 partial:4 |
| 2 | questions_deadline | correct:1 partial:4 | correct:1 partial:4 |
| 3 | rfp_contact | correct:2 partial:3 | correct:2 partial:3 |
| 4 | submission_method | partial:5 | partial:3 wrong:2 |
| 5 | contract_term | correct:1 partial:4 | correct:2 partial:3 |
| 6 | scope_of_deliverables | partial:3 wrong:2 | partial:3 wrong:2 |
| 7 | mandatory_submission_requirements | correct:4 missing:1 | correct:4 wrong:1 |
| 8 | mandatory_technical_requirements | correct:2 partial:2 missing:1 | correct:3 wrong:2 |
| 9 | evaluation_criteria | correct:4 partial:1 | correct:4 partial:1 |
| 10 | minimum_score_threshold | correct:4 wrong:1 | correct:4 wrong:1 |
| 11 | pricing_structure | correct:1 partial:3 wrong:1 | partial:4 wrong:1 |
| 12 | insurance_requirements | correct:3 partial:2 | correct:3 partial:2 |
| 13 | vendor_experience_required | correct:1 partial:2 wrong:2 | correct:2 partial:2 wrong:1 |
| 14 | references_required | correct:4 wrong:1 | correct:4 wrong:1 |
| 15 | data_security_requirements | correct:1 partial:3 wrong:1 | correct:4 wrong:1 |
| 16 | data_hosting_residency | correct:2 partial:2 wrong:1 | correct:3 partial:1 wrong:1 |
| 17 | vendor_demonstration_required | correct:5 | correct:5 |

Notable: fields 7-8 (mandatory requirements lists) show Lift producing 1
outright `missing` answer each where Qwen3.5-9B always returned something
(right or wrong) — consistent with the `cluster_failures: 1` and
`malformed_json_errors: 1` recorded in Lift's `benchmark_summary.json` (Qwen3.5-9B
recorded 0 for both).

---

## SECTION B — older, non-comparable results (11-document corpus, different/larger ground truth)

**These runs used a different document set (up to 20 docs in `docs/`, 11 with
ground truth) and a different, non-identical ground-truth file
(`ground_truth/*.json`, the full-corpus set, not the V2 5-RFP combined file).
They are kept separate deliberately — do not merge these rows with Section A.**

Source: live `grade.py` run recorded in `RFP_CAPSTONE_EVIDENCE.md` §15
(2026-09-22), re-stated here unmodified (not re-run for this collection).

| Backend | Docs graded | Correct | Partial | Wrong | Missing | Total fields | Accuracy |
|---|---:|---:|---:|---:|---:|---:|---:|
| claude-opus-5-text | 1 | 15 | 1 | 1 | 0 | 17 | 88.2% |
| claude-sonnet-5-text | 1 | 16 | 1 | 0 | 0 | 17 | 94.1% |
| gpt-4o-text | 11 | 107 | 48 | 32 | 0 | 187 | 57.2% |
| gpt-5.5-vision | 2 | 26 | 8 | 0 | 0 | 34 | 76.5% |
| k2-horizon-7b-text | 11 | 118 | 43 | 24 | 2 | 187 | 63.1% |
| llama-70b-text | 8 | 71 | 40 | 25 | 0 | 136 | 52.2% |
| qwen3-vl-32b-vision | 9 | 100 | 34 | 16 | 3 | 153 | 65.4% |
| qwen3.5-9b-text | 11 | 114 | 46 | 27 | 0 | 187 | 61.0% |

Per-backend token/latency totals for this corpus were **not aggregated** in the
source evidence file (only recorded per-document per-backend inside each result
JSON — see `benchmarks/results_all_models/<backend>/<doc>.json`, key
`totals.{prompt_tokens,completion_tokens,latency_s}`); computing a corpus-wide
average was out of scope for this collection pass (would require iterating all
result files, which this task did not do to stay strictly read-only/no-recompute).
`claude-opus-5-text`, `claude-sonnet-5-text`, and `gpt-5.5-vision` were run on only
1, 1, and 2 documents respectively — explicitly noted in the source evidence as
used to *produce* ground truth (blind test-then-freeze) or as a late exploratory
add, **not comparable** even within this already-non-comparable section.

`gpt-4o-vision` is registered as a backend in `rfpbench/backends.py` but has no
saved results anywhere in the project — **MISSING**, not run.

### Legacy 5-RFP corpus results directories (results_baseline_v1/v2/v3_fulltext)

`results_baseline_v1/`, `results_v2/`, `results_v3_fulltext/` (all copied into
`benchmarks/`) are earlier, superseded snapshots from the same development
process that produced the numbers above — iterative prompt/pipeline versions,
not additional independent benchmarks. They are included for completeness/audit
trail only; **do not cite their numbers as current results.**

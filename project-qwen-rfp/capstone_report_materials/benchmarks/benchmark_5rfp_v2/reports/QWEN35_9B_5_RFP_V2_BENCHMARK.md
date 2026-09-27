# Qwen3.5-9B 5-RFP V2 Benchmark

## Benchmark Configuration

Model:
QuantTrio/Qwen3.5-9B-AWQ (backend key `qwen3.5-9b-text`)

Endpoint:
http://localhost:8100/v1 (docker container `vllm-bench`, image `vllm/vllm-openai:latest`, `--quantization awq_marlin --dtype half --max-model-len 32768 --gpu-memory-utilization 0.90`)

Ground Truth:
ground_truth_5_rfps_combined_V2.json (sha256 `a26cd8378b680ea60555f59429c5c9750a449dd192b89c3ce78677d66868c03d`) — same read-only split ground truth used for the Lift 5-RFP V2 benchmark (`benchmark_5rfp_v2/ground_truth/`)

Documents:
5 (identical set used for the Lift 5-RFP V2 benchmark)

Fields per document:
17

Total evaluation points:
85

Extraction command:
`./.venv/bin/python run.py -m qwen3.5-9b --docs benchmark_5rfp_v2/docs_selected --out benchmark_5rfp_v2/results --vllm-url http://localhost:8100/v1`

Grading:
`benchmark_5rfp_v2/run_grade.py --backend qwen3.5-9b-text`, which imports and calls the project's existing `grade.py::grade_field()` unmodified — same grading logic, same LLM judge, used for every model graded in this project (including the Lift 5-RFP V2 run, re-verified to reproduce identically before this run).

Note on GPU scheduling: this benchmark reused the A6000 that had `lift-vllm` running from the prior Lift 5-RFP V2 benchmark. `lift-vllm` was stopped and `vllm-bench` (Qwen3.5-9B-AWQ) started in its place to free VRAM — the same swap pattern used earlier in this session, per standing approval. Lift is not running after this benchmark; Qwen3.5-9B-AWQ is.

## Overall Results

| Metric | Result |
|---|---:|
| Correct | 42 |
| Partial | 30 |
| Wrong | 13 |
| Missing | 0 |
| Total | 85 |
| Accuracy | 49.4% |
| Adjusted Accuracy | 67.1% |

Adjusted accuracy = (Correct×1.0 + Partial×0.5) / Total. Secondary metric only.

## Per-Document Results

| Document | Correct | Partial | Wrong | Missing | Total | Accuracy | Latency (s) |
|---|---:|---:|---:|---:|---:|---:|---:|
| AB-2025-02456 (ERP Requirements Analysis, Rocky View County) | 10 | 5 | 2 | 0 | 17 | 58.8% | 56.09 |
| AB-2026-05648 (LMS Platform Support, Olds College) | 5 | 8 | 4 | 0 | 17 | 29.4% | 52.54 |
| City of Medicine Hat - LMS tender | 7 | 8 | 2 | 0 | 17 | 41.2% | 55.44 |
| EN_-_ERP_RFP_24.25.04 (Cowichan Tribes) | 7 | 8 | 2 | 0 | 17 | 41.2% | 50.39 |
| RFP CP-730126 (Generative AI, USask) | 13 | 1 | 3 | 0 | 17 | 76.5% | 81.39 |

## Per-Field Results

| Field | Correct | Partial | Wrong | Missing | Accuracy |
|---|---:|---:|---:|---:|---:|
| submission_deadline | 1 | 4 | 0 | 0 | 20.0% |
| questions_deadline | 1 | 4 | 0 | 0 | 20.0% |
| rfp_contact | 2 | 3 | 0 | 0 | 40.0% |
| submission_method | 0 | 3 | 2 | 0 | 0.0% |
| contract_term | 2 | 3 | 0 | 0 | 40.0% |
| scope_of_deliverables | 0 | 3 | 2 | 0 | 0.0% |
| mandatory_submission_requirements | 4 | 0 | 1 | 0 | 80.0% |
| mandatory_technical_requirements | 3 | 0 | 2 | 0 | 60.0% |
| evaluation_criteria | 4 | 1 | 0 | 0 | 80.0% |
| minimum_score_threshold | 4 | 0 | 1 | 0 | 80.0% |
| pricing_structure | 0 | 4 | 1 | 0 | 0.0% |
| insurance_requirements | 3 | 2 | 0 | 0 | 60.0% |
| vendor_experience_required | 2 | 2 | 1 | 0 | 40.0% |
| references_required | 4 | 0 | 1 | 0 | 80.0% |
| data_security_requirements | 4 | 0 | 1 | 0 | 80.0% |
| data_hosting_residency | 3 | 1 | 1 | 0 | 60.0% |
| vendor_demonstration_required | 5 | 0 | 0 | 0 | 100.0% |

Weakest fields: `submission_method` and `scope_of_deliverables` (0/5 correct each — same pattern as Lift: long free-text answers consistently miss a sub-fact) and `pricing_structure` (0/5, all partial/wrong). Strongest: `vendor_demonstration_required` (5/5), `mandatory_submission_requirements`, `evaluation_criteria`, `minimum_score_threshold`, `references_required`, `data_security_requirements` (4/5 each).

As with Lift, `submission_deadline`/`questions_deadline` show low nominal accuracy but all 8 non-correct verdicts on these two fields are the same known date-regex grader limitation — see **Possible Grader Mismatches**.

## Difficulty Breakdown

| Difficulty | Total | Correct | Partial | Wrong | Missing | Accuracy |
|---|---:|---:|---:|---:|---:|---:|
| Easy | 25 | 13 | 9 | 3 | 0 | 52.0% |
| Medium | 20 | 6 | 11 | 3 | 0 | 30.0% |
| Hard | 40 | 23 | 10 | 7 | 0 | 57.5% |

## Evidence / Groundedness

Same methodology as the Lift benchmark: per-document quote verification against the source PDF (`rfpbench/runner.py::summarise()`), aggregated across the 5 documents.

| Evidence status (fields the model asserted present) | Count |
|---|---:|
| Verified (quote found on claimed page) | 63 |
| Wrong page | 0 |
| Unverified (quote not found anywhere) | 8 |
| No quote given | 0 |
| Total asserted present | 71 |
| Model asserted absent | 14 |

Groundedness (verified + wrong_page) / asserted_present = 63 / 71 = **88.7%**

## Hallucination Analysis

Unsupported / hallucination rate (unverified + no_quote) / asserted_present = 8 / 71 = **11.3%**

Separate content-level hallucinations (asserted `present=true` with a real value where ground truth says the field genuinely does not appear — graded "wrong"): `data_security_requirements` on AB-2025-02456, `vendor_experience_required` on AB-2026-05648 — 2 cases, fewer than Lift's 4 on the same document set.

Qwen3.5-9B also shows the opposite failure mode more often than Lift: 5 cases graded "wrong" where the model said `present=false` (or returned `['null']`/`[]`) for a field ground truth says genuinely is in the document (`mandatory_submission_requirements` and `mandatory_technical_requirements` on AB-2026-05648, `data_hosting_residency` on AB-2026-05648, `scope_of_deliverables` and `mandatory_technical_requirements` on RFP CP-730126) — classified below as "present/absent classification error."

## Token Usage

| Metric | Value |
|---|---:|
| Total prompt/input tokens | 241,863 |
| Total completion/output tokens | 17,043 |
| Total tokens | 258,906 |
| Average tokens per RFP | 51,781.2 |
| Average input tokens per RFP | 48,372.6 |
| Average output tokens per RFP | 3,408.6 |

Roughly 3.5x fewer total tokens than Lift's run on the identical 5 documents (897,191) — Qwen3.5-9B is a text backend (page text only) vs. Lift's vision backend (rendered page images, which cost far more tokens per page).

## Latency

| Document | Latency (s) |
|---|---:|
| AB-2025-02456 | 56.09 |
| AB-2026-05648 | 52.54 |
| City of Medicine Hat | 55.44 |
| EN_-_ERP_RFP_24.25.04 | 50.39 |
| RFP CP-730126 | 81.39 |

Total benchmark latency: 295.85s
Mean latency: 59.17s/doc
Median latency: 55.44s/doc
Fastest document: EN_-_ERP_RFP_24.25.04 (50.39s)
Slowest document: RFP CP-730126 (81.39s)

This is per-document extraction latency (6 field-cluster calls each) as measured by `rfpbench`'s own timers; ~2.8x faster in total than Lift's run on the same 5 documents (840.86s), consistent with a smaller model and text-only (no image-encoding) input. Container/model-load startup time (~290s for this container) is tracked separately and not mixed into per-document latency.

## Error Analysis

43 of 85 fields graded Partial or Wrong (0 Missing — no cluster/JSON failures this run). Full per-field diagnostic table is in `benchmark_5rfp_v2/diagnostics_classified_qwen35_9b.json`. Reason-code tally:

| Likely reason | Count |
|---|---:|
| Under-extraction (real answer, missing some sub-facts) | 20 |
| Grader semantic mismatch (see below) | 12 |
| Present/absent classification error (said absent, GT says present) | 5 |
| Long narrative mismatch (scope_of_deliverables free text) | 4 |
| Over-extraction / hallucinated content | 1 |
| Extraction error (wrong value copied into name field) | 1 |

No cluster failures / malformed JSON this run (0/30 field-cluster calls failed, vs. 1/30 for Lift on the same 5 documents).

The dominant pattern, same as Lift, is **under-extraction**: correct section, real grounded content, missing a sub-fact the judge wants for full credit. Qwen3.5-9B additionally shows a distinct **present/absent classification error** pattern (5 cases) where it returns `present=false`/`['null']`/`[]` for fields ground truth says are genuinely present — this pattern did not appear in Lift's results on the same 5 documents (Lift's 2 "missing" fields were a JSON-parse failure, not a present/absent misclassification).

## Possible Grader Mismatches

12 cases where the model's answer appears semantically equivalent to (or a defensible reading of) ground truth, but `grade.py`'s logic marked it Partial or Wrong. **Grades were not changed.** These mirror exactly the same grader-logic patterns found in the Lift benchmark on this document set (same ground truth, same grader):

**Date/time "invented time" false positives (8 cases)** — ground truth writes the time in plain text, not ISO, so the grader's `gt_has_time` check never fires and the model is downgraded for stating the time that's already in ground truth:
- AB-2025-02456 / submission_deadline — GT `"May 14, 2025, 2:00 PM MST"` vs model `"May 14, 2025, 2:00 PM MST"` (identical)
- AB-2025-02456 / questions_deadline — GT `"April 17, 2025, 2:00 PM MST"` vs model `"April 17, 2025, 2 PM MST"`
- AB-2026-05648 / submission_deadline — GT `"September 9, 2026, before 2:00 PM MT"` vs model `"September 9, 2026 before 2:00:00 PM MT"`
- AB-2026-05648 / questions_deadline — GT `"September 2, 2026, before 2:00 PM MT"` vs model `"September 2, 2026 before 2:00:00 PM MT"`
- City of Medicine Hat / submission_deadline — GT `"May 28, 2026, 2:00 PM local time"` vs model `"May 28, 2026 2:00 PM local time"`
- City of Medicine Hat / questions_deadline — GT `"May 21, 2026, 4:00 PM local time"` vs model `"May 21, 2026 4:00 PM local time"`
- EN_-_ERP_RFP_24.25.04 / submission_deadline — GT `"April 14, 2025, 11:59:59 PM PST"` vs model `"April 14, 2025 11:59:59 PM PST"`
- EN_-_ERP_RFP_24.25.04 / questions_deadline — GT `"March 17, 2025, 11:59:59 PM PST"` vs model `"March 17, 2025 11:59:59 PM PST"`

**Contact-field substring check (2 cases)** — the `contact` comparator requires the entire GT string (split on first comma) to appear verbatim in `json.dumps(answer)`; when GT combines name+email with `"; "` this can never match separate JSON keys even when correctly extracted:
- City of Medicine Hat / rfp_contact — model correctly returned name/email; graded partial for the same structural reason as Lift.
- EN_-_ERP_RFP_24.25.04 / rfp_contact — model correctly returned "Jeremy Elliott" / "procurement@cowichantribes.com"; same issue.

(Note: AB-2026-05648 / rfp_contact is **not** included here — the model itself made a real extraction error, using the email address as the `name` field value, so that one grades correctly as an extraction error, not a grader artifact.)

**Number-type ground truth stored as descriptive text (2 cases)**:
- EN_-_ERP_RFP_24.25.04 / minimum_score_threshold — GT is a list of descriptive strings; model answered `28` (the correct Functional Fit threshold), but `float()` on each GT string always raises, so it's graded "wrong" regardless of the model's answer.
- EN_-_ERP_RFP_24.25.04 / references_required — GT is text `"At least 2 and at most 5"`; model answered `2`, within the stated range, but the same `float(t)` failure grades it "wrong".

## Runtime Errors / Retries

- Malformed JSON errors: 0
- Schema errors: 0
- Cluster failures: 0 of 30 cluster calls
- Retries: 0 observed in the extraction log

## Conclusions

Measured results only, no target-score judgment; both models were graded against the identical 5-document / 85-field ground truth with the identical unmodified grading logic, so this section only reports the head-to-head numbers observed:

- Primary (exact) accuracy: Qwen3.5-9B-AWQ **49.4%** vs Lift **42.4%** on the same 5 RFPs. Adjusted (partial-credit) accuracy: Qwen3.5-9B-AWQ **67.1%** vs Lift **64.7%** — a smaller gap once partial credit is counted.
- Qwen3.5-9B-AWQ had 0 cluster/JSON failures (Lift had 1, costing 2 fields), but showed 5 "present/absent classification error" cases (calling a genuinely-present field absent) that did not occur in Lift's run on the same documents.
- Groundedness/hallucination rates are close: Qwen3.5-9B-AWQ 88.7% grounded / 11.3% hallucination vs Lift 87.0% / 13.0%.
- Qwen3.5-9B-AWQ used ~3.5x fewer tokens and ran ~2.8x faster in total wall-clock extraction time than Lift on the identical 5 documents — expected, since it is a much smaller model reading page text rather than rendered page images.
- The same 12 grader-logic artifacts (date-time regex, contact substring matching, number-vs-text ground truth) recur identically for both models on this document set, since they stem from the ground truth's own value formatting and the shared grading code, not from either model's behavior — worth a manual grading-logic review, but grades were left as-is per instructions.

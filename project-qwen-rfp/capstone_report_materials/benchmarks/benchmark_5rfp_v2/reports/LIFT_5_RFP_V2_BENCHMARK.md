# Lift 5-RFP V2 Benchmark

## Benchmark Configuration

Model:
datalab-to/lift

Endpoint:
http://127.0.0.1:8200/v1 (docker container `lift-vllm`, image `vllm/vllm-openai:latest`, `--max-model-len 32768 --gpu-memory-utilization 0.85 --trust-remote-code`)

Ground Truth:
ground_truth_5_rfps_combined_V2.json (sha256 `a26cd8378b680ea60555f59429c5c9750a449dd192b89c3ce78677d66868c03d`), split read-only into 5 per-document files under `benchmark_5rfp_v2/ground_truth/`

Documents:
5

Fields per document:
17

Total evaluation points:
85

Extraction command:
`./.venv/bin/python run.py -m lift-vision --docs benchmark_5rfp_v2/docs_selected --out benchmark_5rfp_v2/results --lift-url http://127.0.0.1:8200/v1`

Grading:
`benchmark_5rfp_v2/run_grade.py`, which imports and calls the project's existing `grade.py::grade_field()` unmodified (same LLM-judge, same date/number/table comparison logic used by every other model in this project).

## Overall Results

| Metric | Result |
|---|---:|
| Correct | 36 |
| Partial | 38 |
| Wrong | 9 |
| Missing | 2 |
| Total | 85 |
| Accuracy | 42.4% |
| Adjusted Accuracy | 64.7% |

Adjusted accuracy = (Correct×1.0 + Partial×0.5) / Total. This is a secondary metric only — primary accuracy above is exact/correct-only.

## Per-Document Results

| Document | Correct | Partial | Wrong | Missing | Total | Accuracy | Latency (s) |
|---|---:|---:|---:|---:|---:|---:|---:|
| AB-2025-02456 (ERP Requirements Analysis, Rocky View County) | 7 | 6 | 2 | 2 | 17 | 41.2% | 265.99 |
| AB-2026-05648 (LMS Platform Support, Olds College) | 6 | 9 | 2 | 0 | 17 | 35.3% | 108.13 |
| City of Medicine Hat - LMS tender | 6 | 10 | 1 | 0 | 17 | 35.3% | 121.64 |
| EN_-_ERP_RFP_24.25.04 (Cowichan Tribes) | 6 | 9 | 2 | 0 | 17 | 35.3% | 111.87 |
| RFP CP-730126 (Generative AI, USask) | 11 | 4 | 2 | 0 | 17 | 64.7% | 233.23 |

## Per-Field Results

| Field | Correct | Partial | Wrong | Missing | Accuracy |
|---|---:|---:|---:|---:|---:|
| submission_deadline | 1 | 4 | 0 | 0 | 20.0% |
| questions_deadline | 1 | 4 | 0 | 0 | 20.0% |
| rfp_contact | 2 | 3 | 0 | 0 | 40.0% |
| submission_method | 0 | 5 | 0 | 0 | 0.0% |
| contract_term | 1 | 4 | 0 | 0 | 20.0% |
| scope_of_deliverables | 0 | 3 | 2 | 0 | 0.0% |
| mandatory_submission_requirements | 4 | 0 | 0 | 1 | 80.0% |
| mandatory_technical_requirements | 2 | 2 | 0 | 1 | 40.0% |
| evaluation_criteria | 4 | 1 | 0 | 0 | 80.0% |
| minimum_score_threshold | 4 | 0 | 1 | 0 | 80.0% |
| pricing_structure | 1 | 3 | 1 | 0 | 20.0% |
| insurance_requirements | 3 | 2 | 0 | 0 | 60.0% |
| vendor_experience_required | 1 | 2 | 2 | 0 | 20.0% |
| references_required | 4 | 0 | 1 | 0 | 80.0% |
| data_security_requirements | 1 | 3 | 1 | 0 | 20.0% |
| data_hosting_residency | 2 | 2 | 1 | 0 | 40.0% |
| vendor_demonstration_required | 5 | 0 | 0 | 0 | 100.0% |

Weakest fields: `submission_method` (0/5 correct — always graded "partial" for omitting one sub-detail), `scope_of_deliverables` (0/5 — long free-text summaries consistently omit some ground-truth facts). Strongest: `vendor_demonstration_required` (5/5, boolean field), `evaluation_criteria`, `mandatory_submission_requirements`, `minimum_score_threshold`, `references_required` (4/5 each).

Note: `submission_deadline`/`questions_deadline` show low nominal accuracy (20% each) but see **Possible Grader Mismatches** below — 8 of the 8 non-correct verdicts on these two fields are a known grading-regex limitation, not extraction misses; Lift's date+time values were correct in all 8 cases.

## Difficulty Breakdown

| Difficulty | Total | Correct | Partial | Wrong | Missing | Accuracy |
|---|---:|---:|---:|---:|---:|---:|
| Easy | 25 | 13 | 11 | 1 | 0 | 52.0% |
| Medium | 20 | 7 | 10 | 3 | 0 | 35.0% |
| Hard | 40 | 16 | 17 | 5 | 2 | 40.0% |

## Evidence / Groundedness

Methodology: same as prior Lift benchmark runs — per-document quote-verification against the source PDF (`rfpbench/runner.py::summarise()`), aggregated across the 5 documents.

| Evidence status (fields the model asserted present) | Count |
|---|---:|
| Verified (quote found on claimed page) | 66 |
| Wrong page (quote found, different page) | 1 |
| Unverified (quote not found anywhere) | 10 |
| No quote given | 0 |
| Total asserted present | 77 |
| Model asserted absent | 6 |
| Malformed-JSON / no answer (2 fields, 1 cluster) | 2 |

Groundedness (verified + wrong_page) / asserted_present = 67 / 77 = **87.0%**

## Hallucination Analysis

Unsupported / hallucination rate (unverified + no_quote) / asserted_present = 10 / 77 = **13.0%**

Separately, `grade.py` flags 4 fields across the 5 docs where Lift asserted `present=true` with a real value but ground truth says the field genuinely does not appear in the document (hard-graded "wrong" — HALLUCINATED): `data_security_requirements` and `data_hosting_residency` on AB-2025-02456 (an ERP *consulting/readiness* RFP with no cloud-hosting section), `vendor_experience_required` on AB-2026-05648 and RFP CP-730126. These 4 are content-level hallucinations distinct from the quote-grounding hallucination rate above.

## Token Usage

| Metric | Value |
|---|---:|
| Total prompt/input tokens | 874,213 |
| Total completion/output tokens | 22,978 |
| Total tokens | 897,191 |
| Average tokens per RFP | 179,438.2 |
| Average input tokens per RFP | 174,842.6 |
| Average output tokens per RFP | 4,595.6 |

(Measured directly from each cluster call's `prompt_tokens`/`completion_tokens`, summed per document, then across the 5 documents — no estimation.)

## Latency

| Document | Latency (s) |
|---|---:|
| AB-2025-02456 | 265.99 |
| AB-2026-05648 | 108.13 |
| City of Medicine Hat | 121.64 |
| EN_-_ERP_RFP_24.25.04 | 111.87 |
| RFP CP-730126 | 233.23 |

Total benchmark latency: 840.86s
Mean latency: 168.17s/doc
Median latency: 121.64s/doc
Fastest document: AB-2026-05648 (108.13s)
Slowest document: AB-2025-02456 (265.99s)

This is per-document extraction latency (6 field-cluster calls each) as measured by `rfpbench`'s own timers; it does not include the ~250s container/model-load startup time recorded separately in `run_manifest.json`, since the harness never mixes the two.

## Error Analysis

49 of 85 fields graded Partial, Wrong, or Missing. Full per-field diagnostic table (document, field, ground truth, Lift answer, grade, likely reason) is in `benchmark_5rfp_v2/diagnostics_classified.json`. Reason-code tally:

| Likely reason | Count |
|---|---:|
| Under-extraction (real answer, missing some sub-facts) | 28 |
| Grader semantic mismatch (see below) | 12 |
| Long narrative mismatch (scope_of_deliverables free text) | 5 |
| Cluster failure (malformed JSON on one cluster call) | 2 |
| Over-extraction / hallucinated content | 1 |
| Extraction error (wrong section pulled) | 1 |

The single **cluster failure**: on `AB-2025-02456`, the `requirements` cluster call returned unparseable JSON (`Expecting value: line 1 column 16748`), so `mandatory_submission_requirements` and `mandatory_technical_requirements` were never answered for that document (both graded Missing). No other cluster failed across the 5 documents × 6 clusters = 30 calls (1/30 cluster failure rate).

The dominant pattern is **under-extraction**: Lift's free-text and list answers are almost always directionally correct and grounded in the right pages, but omit one or more sub-facts the LLM judge expects (e.g. a currency, a maximum-term clause, one insurance line item) — pulling it to "partial" rather than "wrong." This shows up heavily in `submission_method`, `contract_term`, `pricing_structure`, `vendor_experience_required`, `data_hosting_residency`, and the two LIST/TABLE fields (`mandatory_technical_requirements`, `insurance_requirements`).

## Possible Grader Mismatches

12 cases where Lift's answer appears semantically equivalent (or a defensible reading of) ground truth, but `grade.py`'s existing logic marked it Partial or Wrong. **Grades were not changed** — listed here for manual review only, per instructions.

**Date/time "invented time" false positives (8 cases)** — `grade.py`'s datetime comparator only detects that ground truth encodes a time-of-day via an ISO regex (`T\d{2}:\d{2}`); every ground-truth value in this V2 set writes the time in plain text (e.g. `"May 14, 2025, 2:00 PM MST"`), so `gt_has_time` is always `False` here, and Lift is downgraded to "partial" for stating the literal time that's already in the ground truth string:
- AB-2025-02456 / submission_deadline — GT `"May 14, 2025, 2:00 PM MST"` vs Lift `"May 14, 2025, 2:00 PM MST"` (identical)
- AB-2025-02456 / questions_deadline — GT `"April 17, 2025, 2:00 PM MST"` vs Lift `"April 17, 2025, 2 PM MST"`
- AB-2026-05648 / submission_deadline — GT `"September 9, 2026, before 2:00 PM MT"` vs Lift `"September 9, 2026 before 2:00:00 PM MT"`
- AB-2026-05648 / questions_deadline — GT `"September 2, 2026, before 2:00 PM MT"` vs Lift `"September 2, 2026 before 2:00:00 PM MT"`
- City of Medicine Hat / submission_deadline — GT `"May 28, 2026, 2:00 PM local time"` vs Lift `"May 28, 2026 2:00 PM local time"`
- City of Medicine Hat / questions_deadline — GT `"May 21, 2026, 4:00 PM local time"` vs Lift `"May 21, 2026 4:00 PM local time"`
- EN_-_ERP_RFP_24.25.04 / submission_deadline — GT `"April 14, 2025, 11:59:59 PM PST"` vs Lift `"April 14, 2025 11:59:59 PM PST"`
- EN_-_ERP_RFP_24.25.04 / questions_deadline — GT `"March 17, 2025, 11:59:59 PM PST"` vs Lift `"March 17, 2025 11:59:59 PM PST"`

**Contact-field substring check (2 cases)** — the `contact` type comparator requires the *entire* ground-truth string (split on the first comma) to appear verbatim inside `json.dumps(answer)`; when ground truth combines name+email with `"; "` and Lift correctly extracts them into separate `name`/`email` JSON keys, the literal substring can never match even though the contact was extracted correctly:
- City of Medicine Hat / rfp_contact — Lift correctly returned name "Joanne Bruneau-Carter" + email "joabru@medicinehat.ca"; graded partial because the GT string also contains a trailing procedural sentence about the bids&tenders portal that can't literally appear in a name/email dict.
- EN_-_ERP_RFP_24.25.04 / rfp_contact — Lift correctly returned "Jeremy Elliott" / "procurement@cowichantribes.com"; graded partial for the same structural reason.

**Number-type ground truth stored as descriptive text (2 cases)** — field type is `number`, but the ground-truth value is a non-numeric string/list, so `float(t)` or `float(candidate)` always raises and the field is graded "wrong" regardless of Lift's answer:
- EN_-_ERP_RFP_24.25.04 / minimum_score_threshold — GT is a list of descriptive strings (`["Functional Fit: 28/35 (80%)", ...]`); Lift answered the bare number `28`, which is the correct Functional Fit threshold, but grading tries `float()` on each descriptive GT string and always fails.
- EN_-_ERP_RFP_24.25.04 / references_required — GT is the text `"At least 2 and at most 5"`; Lift answered `5`, which is within the stated range, but `float("At least 2 and at most 5")` raises and the field is graded "wrong".

## Token Usage / Latency / Runtime Errors — Summary

See sections above for full breakdown.

## Runtime Errors / Retries

- Malformed JSON errors: 1 (see Error Analysis / cluster failure above)
- Schema errors: 0
- Cluster failures: 1 of 30 cluster calls (5 docs × 6 clusters)
- Retries: 0 (the harness does not retry on cluster failure; the failed cluster's fields are simply left unanswered)

## Conclusions

Measured results only, no target-score judgment:

- Primary (exact) accuracy on this 5-document / 85-field set: **42.4%**; adjusted (partial-credit) accuracy: **64.7%**.
- Groundedness of asserted-present answers: 87.0%; quote-level hallucination rate: 13.0%; 4 additional content-level hallucinations where Lift asserted a field was present when ground truth says it is not.
- The largest source of non-"correct" grades (28 of 49) is under-extraction on long free-text/list fields — Lift consistently finds the right section but omits some of the sub-facts an LLM judge expects for full credit, rather than being wrong or fabricating.
- 1 of 30 field-cluster calls returned malformed JSON, costing 2 of 85 fields ("missing").
- 12 of 49 non-correct grades are flagged as possible grader artifacts (date-time regex, contact substring matching, number-vs-text ground truth) rather than genuine extraction failures — worth a manual grading-logic review, but grades were left as-is per instructions.

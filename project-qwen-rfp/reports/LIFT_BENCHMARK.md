# Lift Benchmark

**INTERIM LIFT BENCHMARK.** No file, filename, or string "BeamData" exists anywhere
in this project (confirmed by `grep -ril beamdata`, no matches - consistent with
`RFP_CAPSTONE_EVIDENCE.md` §2/§9). No official "five BeamData RFPs" set could be
identified, so per instructions this run was **not** guessed at; it instead uses
the same real-RFP + ground-truth corpus the existing benchmark already uses (10
documents), with the synthetic smoke-test document excluded from the formal score
exactly as the project's own README already excludes it. Generated 2026-09-22.

## Model

`datalab-to/lift` - Datalab's 9B parameter Qwen3.5-based vision-language model,
purpose-built for schema-constrained document/PDF extraction (not a general
chatbot). License: Apache-2.0 code, OpenRAIL-M-derived weights (see Limitations).

## Environment

| Item | Value |
|---|---|
| GPU | NVIDIA RTX A6000, 49,140 MiB total |
| VRAM used by Lift | ~19.6 GB (41,079 MiB used / 7,591 MiB free system-wide with Lift as the only model loaded) |
| CUDA | 12.4 (driver 550.90.12) |
| Serving method | Docker, `vllm/vllm-openai:latest`, same pattern as the project's existing local backends - **not** the `lift-pdf` pip/`lift_vllm` CLI wrapper (see Limitations for why) |
| vLLM version | v0.29.0 (same image already used for `vllm-bench`/Qwen) |
| Lift checkpoint | `datalab-to/lift` @ HF revision `3129597900eb6f84fb4f2c0b240f9a7cfddae595`, resolved architecture `Qwen3_5ForConditionalGeneration` |
| Dtype | bfloat16 (model default; no explicit `--dtype` override) |
| Quantization | none |
| Context limit | `--max-model-len 32768` |
| Model endpoint | `http://127.0.0.1:8200/v1`, container `lift-vllm`, served-model-name `datalab-to/lift` |
| Qwen (`vllm-bench`) state during this run | **stopped** (not removed) to free VRAM - see `runtime_backup/` for its exact restart config |

## Dataset

- **Documents evaluated:** 10 (the full existing real-RFP corpus that has ground
  truth, minus the synthetic smoke-test doc - see list below)
- **Fields per document:** 17 (unmodified project schema, `rfpbench/fields.py`)
- **Total field-level evaluation points:** 170 (10 x 17)

LIFT BENCHMARK DOCUMENTS:
1. 01_Reference_Data_Management_Services_RFP.pdf
2. 02_Certification_Testing_Platform_and_Services_RFP.pdf
3. 03_Asset_Management_GIS_IT_Consulting_RFP.pdf
4. 04_Data_Centre_Download_Integration_Services_RFP.pdf
5. AB-2025-02456-RFP #25-004ERP Requirements Analysis and Readiness Review_Final (1).pdf
6. AB-2026-05648-197-2027 RFP Learning Management System (LMS) Platform  Support (2).pdf
7. City of Medicine Hat - LMS tender.pdf
8. EN_-_ERP_RFP_24.25.04.pdf
9. RFP CP-730126 Generative AI RFP (4).pdf
10. RFP-2026-8-PR-CASCADE-Updated-with-QAs-1.pdf

Ground truth is frozen and was not modified, read, or referenced by Lift's
extraction prompt/schema at any point - it was only used afterward, by the
project's existing `grade.py`, exactly as for every other backend.

## Overall Results

Graded with the project's own unmodified `grade.py` (`--exclude synthetic`).

| Metric | Result |
|---|---:|
| Correct | 102 |
| Partial | 39 |
| Wrong | 23 |
| Missing | 6 |
| Total | 170 |
| Accuracy | 60.0% |

## Accuracy by Difficulty

Ground-truth difficulty labels, unmodified.

| Difficulty | Correct | Partial | Wrong | Accuracy |
|---|---:|---:|---:|---:|
| Easy | 47 | 4 | 3 | 87.0% |
| Medium | 31 | 21 | 5 | 50.8% |
| Hard | 24 | 14 | 15 | 43.6% |

Same pattern as every other backend in this project: strong on easy fields,
substantially weaker on the deliberate "hard" traps in ground truth.

## Per-Document Results

| Document | Correct | Partial | Wrong | Missing | Accuracy | Latency (s) |
|---|---:|---:|---:|---:|---:|---:|
| 01_Reference_Data_Management_Services_RFP | 11 | 4 | 2 | 0 | 64.7% | 165.1 |
| 02_Certification_Testing_Platform_and_Services_RFP | 11 | 3 | 3 | 0 | 64.7% | 98.7 |
| 03_Asset_Management_GIS_IT_Consulting_RFP | 11 | 0 | 2 | 4 | 64.7% | 262.8 |
| 04_Data_Centre_Download_Integration_Services_RFP | 10 | 3 | 4 | 0 | 58.8% | 79.5 |
| AB-2025-02456-RFP #25-004ERP Requirements Analysis and Readiness Review_Final (1) | 8 | 4 | 3 | 2 | 47.1% | 250.2 |
| AB-2026-05648-197-2027 RFP Learning Management System (LMS) Platform Support (2) | 9 | 8 | 0 | 0 | 52.9% | 104.0 |
| City of Medicine Hat - LMS tender | 8 | 7 | 2 | 0 | 47.1% | 107.2 |
| EN_-_ERP_RFP_24.25.04 | 14 | 1 | 2 | 0 | 82.4% | 104.3 |
| RFP CP-730126 Generative AI RFP (4) | 11 | 4 | 2 | 0 | 64.7% | 131.6 |
| RFP-2026-8-PR-CASCADE-Updated-with-QAs-1 | 9 | 5 | 3 | 0 | 52.9% | 85.2 |
| **Total / average** | **102** | **39** | **23** | **6** | **60.0%** | **138.9 avg** |

Latency is per-document total across all 6 field clusters (i.e. 6 model calls),
measured directly from `totals.latency_s` in each saved result file - not
per-cluster and not estimated.

## Token Usage

Measured directly from vLLM's own `usage` field on every response (same
mechanism as every other local backend in this project).

| Metric | Value |
|---|---:|
| Total prompt tokens | 1,548,499 |
| Total completion tokens | 37,998 |
| Total tokens | 1,586,497 |
| Documents | 10 |
| Avg prompt tokens/doc | 154,850 |
| Avg completion tokens/doc | 3,800 |

Cost: $0.00 (local model - vLLM's OpenAI-compatible server does not charge per
token; `PRICING` in `backends.py` has no entry for `lift`, matching how the
other local backends are already priced at $0).

## Evidence / Hallucination Analysis

Using the project's existing mechanical quote-in-page verification
(`rfpbench/document.find_quote`, unmodified) - not a Lift-specific check.

| Evidence status | Count |
|---|---:|
| Verified (quote found on claimed page) | 120 |
| Wrong page (quote found, but on a different page than claimed) | 5 |
| Unverified (quote claimed but not found anywhere in the document) | 13 |
| No quote (claimed present, offered no evidence) | 0 |
| Absent (field correctly reported absent) | 26 |

- **Asserted** (present + some evidence claim): 138
- **Groundedness** (verified + wrong_page) / asserted: **90.6%**
- **Hallucination rate** (unverified + no_quote) / asserted: **9.4%**

This is a pre-ground-truth signal (whether a claimed quote is real, independent
of whether the *value* is correct) - it is not the same number as benchmark
accuracy above, and both are reported because they measure different things.

## Field-Level Performance

| # | Field | Correct | Partial | Wrong | Missing | Total | Accuracy |
|---|---|---:|---:|---:|---:|---:|---:|
| 1 | submission_deadline | 10 | 0 | 0 | 0 | 10 | 100.0% |
| 2 | questions_deadline | 9 | 0 | 1 | 0 | 10 | 90.0% |
| 3 | rfp_contact | 9 | 0 | 1 | 0 | 10 | 90.0% |
| 4 | submission_method | 4 | 5 | 1 | 0 | 10 | 40.0% |
| 5 | contract_term | 3 | 3 | 4 | 0 | 10 | 30.0% |
| 6 | scope_of_deliverables | 1 | 8 | 1 | 0 | 10 | 10.0% |
| 7 | mandatory_submission_requirements | 8 | 1 | 0 | 1 | 10 | 80.0% |
| 8 | mandatory_technical_requirements | 3 | 1 | 5 | 1 | 10 | 30.0% |
| 9 | evaluation_criteria | 9 | 1 | 0 | 0 | 10 | 90.0% |
| 10 | minimum_score_threshold | 10 | 0 | 0 | 0 | 10 | 100.0% |
| 11 | pricing_structure | 4 | 5 | 0 | 1 | 10 | 40.0% |
| 12 | insurance_requirements | 7 | 2 | 0 | 1 | 10 | 70.0% |
| 13 | vendor_experience_required | 2 | 5 | 3 | 0 | 10 | 20.0% |
| 14 | references_required | 6 | 0 | 3 | 1 | 10 | 60.0% |
| 15 | data_security_requirements | 4 | 5 | 1 | 0 | 10 | 40.0% |
| 16 | data_hosting_residency | 5 | 3 | 2 | 0 | 10 | 50.0% |
| 17 | vendor_demonstration_required | 8 | 0 | 1 | 1 | 10 | 80.0% |

Structured/high-signal fields (dates, contact, thresholds, evaluation table)
score highest; free-text narrative fields that require judging semantic
completeness against a rubric (`scope_of_deliverables`, `contract_term`,
`vendor_experience_required`) score lowest - the same shape of weakness the
project has already documented for its other backends on these same fields.

## Errors

- **Runtime errors:** 0 (container never crashed or restarted during the run)
- **Malformed JSON (unparseable, both attempts including the temperature-bump
  retry already built into `Backend.call()`):** 2 of 60 clusters (3.3%)
  - `03_Asset_Management_GIS_IT_Consulting_RFP :: commercial_pricing` -
    `Expecting ',' delimiter: line 1 column 4150`
  - `AB-2025-02456-RFP ... :: requirements` -
    `Unterminated string starting at: line 1 column 6158`
- **Schema failures:** 0 (schema itself was always accepted; the 2 failures
  above are decode-time truncation/malformation of the completion, not schema
  rejection)
- **Page/input failures:** 0 (all 10 PDFs loaded and rendered; no context-length
  overflow at the 14-page vision cap already used for other vision backends)
- **Retries:** the existing single-retry-at-temperature-0.3 mechanism
  (`Backend.call()`, unmodified) fired on both failures above; neither
  recovered nor triggered partial-JSON salvage (the salvage routine could not
  find a completed top-level field boundary in either raw completion), so both
  clusters' fields (6 total, all in the `commercial_pricing`/`requirements`
  clusters for those two documents) are recorded as `missing` rather than a
  guessed or fabricated value.

## Limitations

- **Serving method deviates from Lift's own recommended CLI.** The model card
  recommends `pip install lift-pdf` + `lift_vllm` (which launches a
  GPU-preset-tuned Docker container itself) or `lift_extract`. That package
  requires **Python >= 3.12**; this host only has Python 3.10.12 and no
  `python3.12`/`uv` available, so the `lift-pdf` CLI could not be installed.
  Instead, this integration used the alternative the model card itself
  documents - "You can also start your own vLLM server with the
  `datalab-to/lift` model" - via the exact same `vllm/vllm-openai:latest`
  Docker pattern this project already uses for its other local models. This
  reuses the project's one call path (OpenAI-compatible chat completions +
  `response_format=json_schema`) with **no new client code**, but it also
  means none of `lift_vllm`'s GPU-specific batch-size tuning (`--gpu a100-80`
  etc.) was applied - only vLLM's own defaults plus this project's existing
  `--gpu-memory-utilization 0.85` convention. The RTX A6000 is not in Lift's
  documented list of tuned presets (h100/a100-80/a100/l40s/a10/l4/4090/3090/t4).
- **Schema shape vs. Lift's own guidance.** Lift's docs recommend avoiding
  `anyOf`/`oneOf`/`$ref` in schemas passed to it, since its schema-constrained
  decoder skips (falls back to best-effort on) schemas it cannot compile. This
  project's existing 17-field schema (`rfpbench/schema.py`, unmodified, shared
  by every backend) uses `Optional[...]` fields (which compile to `anyOf` with
  null) and `$ref` for nested list-item models (`CriterionRow`,
  `InsuranceRow`), for the same reasons every other backend already uses it.
  The two malformed-JSON failures above are consistent with this: Lift's
  constrained decoding may not have been fully engaged for those two calls,
  falling back to closer-to-free-form generation that can still break mid-JSON
  under the same infinite-whitespace-loop pathology `backends.py` already
  documents for other vLLM-served models. This was not special-cased or worked
  around; the project's existing generic retry/salvage path handled it exactly
  as it does for the other backends, and where it still failed, those fields
  are correctly recorded as `missing`, not repaired or guessed.
- **Licensing.** Lift's weights carry a modified OpenRAIL-M license: free for
  research, personal use, and startups under $5M funding/revenue; commercial
  self-hosting beyond that requires a paid license from Datalab. This run is a
  benchmark/research comparison for a capstone project, not a production
  deployment.
- **Sample size vs. some other backends.** `claude-opus-5-text`,
  `claude-sonnet-5-text` (1 doc each) and `gpt-5.5-vision` (2 docs) were run on
  far fewer documents than `lift-vision` (10 docs) - see the comparison table
  below; their accuracy numbers are not directly comparable to Lift's for that
  reason, independent of anything about Lift itself.
- **No independent verification of the 90.2% field-accuracy figure Datalab
  publishes for Lift.** That number comes from Datalab's own 225-document
  benchmark, a different, larger, and not-inspected corpus; it is not directly
  comparable to the 60.0% measured here, which is against this project's own
  10-document RFP corpus and its own (LLM-authored, not independently
  human-validated) ground truth and grading rubric.

## Comparison to Existing Results

Built entirely from already-saved `results/*/*.json` files via the project's own
unmodified `grade.py` and `report.py` - **no existing backend was rerun**. Every
row below other than `lift-vision` reflects extraction runs that predate this
task.

**Sample sizes differ across backends - this is not an apples-to-apples
comparison.** In particular: `claude-opus-5-text`, `claude-sonnet-5-text` (1 doc
each, originally run to help produce ground truth) and `gpt-5.5-vision` (2 docs)
have far fewer graded documents than the rest; their accuracy figures should not
be read against backends graded on 7-10 documents. `llama-70b-text` (7 docs) and
`qwen3-vl-32b-vision` (8 docs) also have fewer documents than `lift-vision`,
`gpt-4o-text`, `k2-horizon-7b-text`, and `qwen3.5-9b-text` (10 docs each).

| Backend | Docs | Correct | Partial | Wrong | Missing | Fields | Accuracy |
|---|---:|---:|---:|---:|---:|---:|---:|
| claude-sonnet-5-text | 1 | 16 | 1 | 0 | 0 | 17 | 94.1% |
| claude-opus-5-text | 1 | 15 | 1 | 1 | 0 | 17 | 88.2% |
| gpt-5.5-vision | 2 | 26 | 8 | 0 | 0 | 34 | 76.5% |
| qwen3-vl-32b-vision | 8 | 85 | 35 | 16 | 0 | 136 | 62.5% |
| **lift-vision** | **10** | **102** | **39** | **23** | **6** | **170** | **60.0%** |
| k2-horizon-7b-text | 10 | 102 | 42 | 24 | 2 | 170 | 60.0% |
| qwen3.5-9b-text | 10 | 99 | 44 | 27 | 0 | 170 | 58.2% |
| gpt-4o-text | 10 | 91 | 47 | 32 | 0 | 170 | 53.5% |
| llama-70b-text | 7 | 59 | 36 | 24 | 0 | 119 | 49.6% |

Note: these per-backend numbers were recomputed live from `grade.py --exclude
synthetic` for this report, so every backend's totals are consistently measured
against the same 10-document, synthetic-excluded corpus Lift used - this
produces slightly different absolute counts than the numbers captured in
`RFP_CAPSTONE_EVIDENCE.md` §15 (which included the synthetic document in some
totals), but changes no underlying result file and reruns no model.

**Lift's headline number (60.0%) sits in the middle of the pack among the
10-document backends** - essentially tied with `k2-horizon-7b-text`
(also 60.0%, on the same 10 documents), slightly ahead of `qwen3.5-9b-text`
(58.2%) and `gpt-4o-text` (53.5%), and behind `qwen3-vl-32b-vision` (62.5%, but
on only 8 documents). This is a single measurement on one 10-document corpus
with an LLM-authored (not independently human-validated) ground truth and
grading rubric - not a general claim about Lift's capability, and not the final
formal comparison, which per instructions should wait for a shared, officially
identified benchmark set evaluated under one protocol.

**No winner is declared.** Lift is a purpose-built extraction model with real,
measured advantages this table does not fully capture (evidence/quote
grounding was not part of Datalab's own published benchmark methodology, and
Lift's 90.6% groundedness here is comparable to or better than several other
backends' historical groundedness figures) as well as real, measured weaknesses
(free-text narrative fields, and 2 of 60 clusters breaking JSON decoding). Both
belong in the record without resolving to a single label.

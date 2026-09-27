# Benchmark Method — derived directly from project code

Every claim below is derived from reading the actual source files, cited by path/line.
Nothing here is invented. Source files are copied verbatim into `code/`.

---

## 1. The 17 fields

Source: `rfpbench/fields.py` (`FIELDS` tuple), copied to `code/rfpbench_full/fields.py`.

| # | key | label | type | cluster |
|---|---|---|---|---|
| 1 | submission_deadline | Submission Deadline (date & time) | datetime | timeline_contact |
| 2 | questions_deadline | Deadline for Questions / Inquiries | datetime | timeline_contact |
| 3 | rfp_contact | RFP Contact (name and/or email) | contact | timeline_contact |
| 4 | submission_method | Submission Method / Portal | text | timeline_contact |
| 5 | contract_term | Contract Term / Duration (incl. renewal options) | text | scope_term |
| 6 | scope_of_deliverables | Scope of Deliverables / Services Requested | text | scope_term |
| 7 | mandatory_submission_requirements | Mandatory Submission Requirements | list | requirements |
| 8 | mandatory_technical_requirements | Mandatory Technical Requirements | list | requirements |
| 9 | evaluation_criteria | Evaluation Criteria & Weighting | table | evaluation |
| 10 | minimum_score_threshold | Minimum Score Threshold to Advance | number | evaluation |
| 11 | pricing_structure | Pricing Structure / Cost Submission Requirements | text | commercial_pricing |
| 12 | insurance_requirements | Minimum Insurance Coverage Requirements | table | commercial_pricing |
| 13 | vendor_experience_required | Required Vendor Experience / Qualifications | text | commercial_compliance |
| 14 | references_required | Number of References Required | number | commercial_pricing |
| 15 | data_security_requirements | Data Security / Privacy Compliance Requirements | list | commercial_compliance |
| 16 | data_hosting_residency | Data Hosting / Residency Requirements | text | commercial_compliance |
| 17 | vendor_demonstration_required | Vendor Demonstration Requirement | boolean | commercial_pricing |

Fields are grouped into **6 clusters** (`CLUSTERS` in `fields.py`): `timeline_contact`,
`scope_term`, `requirements`, `evaluation`, `commercial_pricing`, `commercial_compliance`.
Each cluster is one model call against one page selection (`rfpbench/schema.py`
`CLUSTER_MODELS`). The `commercial` cluster was split into `commercial_pricing` /
`commercial_compliance` on 2026-09-22 after vision backends were observed to
truncate mid-generation on the larger combined cluster.

Every field also carries a `guidance` string (goes verbatim into the prompt) with
extensive, dated comments in the source recording specific failure modes found
during development (decoy lists, trap fields, missing-value handling). See
`code/rfpbench_full/fields.py` for the full text — not reproduced here to avoid
duplicating ~350 lines of documented prompt-engineering history.

## 2. Prompt / system instructions

Source: `rfpbench/prompts.py`.

**One shared template for every model.** Only the modality (text vs. rendered page
images) varies; there is deliberately no per-model prompt tuning, so the benchmark
measures model capability rather than prompt-engineering effort per model.

The system prompt (`SYSTEM` constant, `prompts.py:20-69`) establishes 6 rules:
1. Extract only what is explicitly stated — never infer or pattern-complete.
2. Absent (`present=false`, `value=null`) is a valid, common, correct answer.
3. Every `present=true` answer must cite a page number and a verbatim quote —
   mandatory, mechanically checked.
4. Quotes must be copied character-for-character, not paraphrased.
5. Page numbers refer to the page markers given in the prompt, not the document's
   own printed footer numbers.
6. Where a value is restated (e.g. an addendum), use the governing occurrence.

A single worked example (a different, unrelated RFP) is included once to calibrate
depth/format, explicitly including a case where the correct answer is `absent`
despite a nearby scoring table that could tempt a fabricated threshold.

Per-call user message (`build_messages()`, `prompts.py:72-106`): document id, the
list of page numbers shown, the field block (key/label/guidance for that cluster's
fields), and either page-images-with-page-markers (vision) or extracted page text
(text modality).

**A second "verify" pass exists** (`build_verify_messages()` / `VERIFY_SYSTEM`,
`prompts.py:109-162`): a separate call that re-reads the same pages plus the first
draft, asked only to fill gaps (missed second facts in the same sentence, truncated
list items) without contradicting or removing anything already correct.

## 3. Output JSON schema (the extraction contract)

Source: `rfpbench/schema.py`.

Every field answer is one shared shape: `{present: bool, value, page: int|null,
quote: str|null, confidence: float}` (some types add extra keys — `NumberAnswer`
adds `unit`; `DateTimeAnswer` adds `raw`; `ContactAnswer` replaces `value` with
`name`/`email`/`phone`/`title`; `list`/`table` types nest structured rows —
`CriterionRow{category, weight, unit}` for evaluation criteria,
`InsuranceRow{coverage_type, amount, currency, basis}` for insurance).

Enforced via Pydantic `BaseModel` with `extra="forbid"` (`_Strict` base class),
compiled to a JSON schema (`json_schema()`) with `_inline_required()` forcing every
property into `required` and `additionalProperties: false` at every nesting level —
required for OpenAI strict structured outputs and used as vLLM's `guided_json` for
local models. One schema per cluster (`CLUSTER_MODELS` dict), not one schema for
all 17 fields at once.

## 4. Present/absent representation

`present: bool` on every answer. `present=false` means "not specified in the shown
pages"; `value` is `null` (or `[]` for list/table types) in that case. This is a
first-class, explicitly-encouraged answer, not an error state (see prompt rule 2
above).

## 5. Evidence / quotes / pages

Every `present=true` answer must carry `page` (1-based, matching the page markers
shown in the prompt — not the document's own printed page numbers) and `quote`
(verbatim source text). This is checked **mechanically, with no ground truth
needed**, by `rfpbench.document.find_quote()` against the actual PDF page text,
invoked from `_check_evidence()` in `rfpbench/runner.py:144-171`. The result is one
of 5 statuses, attached to the answer as `_evidence.status`:

| status | meaning |
|---|---|
| `verified` | quote found, on the exact page cited |
| `wrong_page` | quote is real but the cited page number is wrong |
| `unverified` | quote occurs nowhere in the document — fabricated |
| `no_quote` | claimed present, gave no quote at all |
| `absent` | model itself said the field is not in the document |

Two per-document quality metrics are computed from these counts
(`summarise()`, `rfpbench/runner.py:174-193`), over `asserted = verified +
wrong_page + unverified + no_quote` (fields the model actually claimed to find):

```
groundedness       = (verified + wrong_page) / asserted
hallucination_rate = (unverified + no_quote) / asserted
```

These are computed **before and independent of ground truth** — they measure
whether an assertion is backed by a real quote in the source PDF, not whether the
answer is factually correct per the ground truth.

## 6. Retries

Source: `rfpbench/backends.py` (`Backend.call()`, comments at lines ~160-195).

On an unparseable-JSON response, the call is retried **once**, at
`temperature=0.3` (root cause documented in the code: certain vLLM guided-decoding
outputs entered an infinite whitespace-repetition loop at the default temperature).
If the retry also fails, a partial-JSON salvage routine (`_salvage_partial_json()`,
`backends.py:31-68`) walks the longer of the two raw completions and recovers
whichever top-level fields finished generating before the break, rather than
discarding the entire cluster for one stuck field.

## 7. Malformed JSON handling

Covered by the same retry + salvage path above. `_salvage_partial_json()` scans
brace/bracket depth and string state character-by-character, and truncates the text
at the last point a top-level field's value fully closed, then re-parses that
truncated prefix as complete JSON. If that also fails to parse, the field(s) still
mid-generation are simply missing from the result (graded as `missing`, see below)
rather than crashing the run.

## 8. Grading

Source: `grade.py` (`grade_field()`, `_compare_values()`), reused unmodified by the
final 5-RFP V2 benchmark's own grader `benchmark_5rfp_v2/run_grade.py` (`import
grade as G; G.grade_field(...)` — confirmed at `run_grade.py:21,60`, not a
reimplementation).

Grading is per-field, comparing one model's answer to the hand/LLM-written ground
truth entry for that field:

- **datetime**: parsed via `dateutil.parser` with corpus-specific timezone
  abbreviations and an "H.MM AM/PM"→"H:MM AM/PM" normalization fix; only calendar
  **date** is compared (`.date()`), never time-of-day, unless the model invented a
  time the ground truth never states (downgrades a date match to `partial`).
- **number**: exact float equality against ground truth, or against any one of a
  list of accepted values when ground truth records multiple valid readings of the
  same document (e.g. several stated per-category thresholds).
- **boolean**: exact equality.
- **contact**: correct if the ground-truth email address (or, if none, a name-token
  match) appears anywhere in the model's answer.
- **list / table**: an LLM judge (`rfpbench.judge.llm_judge_list`, cached in
  `.judge_cache.json`) scores recall of ground-truth items against the model's
  list, independent of item segmentation/wording; falls back to fuzzy
  token-set-ratio ≥65 matching if the judge call fails. `recall ≥ 0.8` → correct,
  `≥ 0.4` → partial, else wrong.
- **text** (free-text fields): an LLM judge (`rfpbench.judge.llm_judge`) compares
  meaning, not word overlap; falls back to fuzzy token-set-ratio (`≥70` correct,
  `≥40` partial, else wrong) if the judge call fails.

### Definitions

- **Correct**: ground truth says absent and the model says absent; OR ground truth
  says present and the model's value passes the type-specific comparison above
  (exact match / date match / judge verdict "correct").
- **Partial**: value comparison lands in the judge's/fuzzy-matcher's middle band
  (partial list/table recall 0.4–0.8, free-text similarity 40–70, or a judge
  "partial" verdict); also used when a date is right but an invented time is
  present.
- **Wrong**: ground truth says present but the model said absent with no rescuable
  content (`"model said absent, but the field is genuinely in the document"`);
  ground truth says absent but the model asserted a value (`"HALLUCINATED a
  value..."`); or the value comparison lands below the wrong-threshold band.
- **Missing**: the model produced no answer object for that field at all (distinct
  from an explicit `present=false` answer).

One rescue rule: if `present=false` but `value` contains real, non-null-placeholder
content (a self-contradiction some vLLM guided-JSON outputs produced), the answer
is graded anyway on its value rather than auto-failed as wrong
(`grade_field()`/`_has_real_content()`, `grade.py:87-137`).

### Formulas

```
Accuracy           = correct / total_fields_graded
```
(`grade.py:354` — `acc = counts["correct"] / total`; identical definition in
`benchmark_5rfp_v2/run_grade.py:120` — `overall["correct"] / total_all`.)

**Two different "adjusted"/lenient metrics exist in this codebase — do not conflate
them:**

- In `grade.py` (the original whole-corpus grader), the lenient column is labeled
  `+grounded` and is defined as:
  ```
  grounded_accuracy = (correct + grounded_partial) / total
  ```
  where `grounded_partial` counts only `partial`-verdict answers whose citation was
  independently mechanically `verified` against the source PDF (`grade.py:331-360`).

- In `benchmark_5rfp_v2/run_grade.py` (the final 5-RFP V2 benchmark's own grader,
  used to produce `benchmark_summary*.json` and the two `reports/*.md` files), the
  reported `adjusted_accuracy` is a simple partial-credit formula:
  ```
  adjusted_accuracy = (correct + 0.5 * partial) / total
  ```
  (`run_grade.py:121`, confirmed identically in the narrative report text,
  `reports/LIFT_5_RFP_V2_BENCHMARK.md`: *"Adjusted accuracy = (Correct×1.0 +
  Partial×0.5) / Total. This is a secondary metric only — primary accuracy above is
  exact/correct-only."*)

  **This is the "Adjusted Accuracy" reported for the final 5-RFP V2 benchmark
  numbers in `FINAL_BENCHMARK_FACTS.md`.**

```
Groundedness       = (verified + wrong_page) / (verified + wrong_page + unverified + no_quote)
Hallucination rate = (unverified + no_quote) / (verified + wrong_page + unverified + no_quote)
```
(`rfpbench/runner.py:184-193`, computed per document per backend, pre-ground-truth,
from the mechanical quote-verification step described in §5 above.)

---

*Derived entirely from reading `rfpbench/fields.py`, `rfpbench/schema.py`,
`rfpbench/prompts.py`, `rfpbench/backends.py`, `rfpbench/document.py`,
`rfpbench/runner.py`, `grade.py`, and `benchmark_5rfp_v2/run_grade.py`, all copied
into `code/` alongside this file.*

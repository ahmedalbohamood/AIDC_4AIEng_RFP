# RFP field-extraction benchmark

Which of three models best extracts 17 specified fields from RFP documents:

| Backend key | Model | Input |
|---|---|---|
| `gpt-4o-text` | GPT-4o (API) | extracted page text |
| `gpt-4o-vision` | GPT-4o (API) | rendered page images |
| `qwen3-vl-32b` | Qwen3-VL-32B (local vLLM) | rendered page images |
| `llama-70b` | Llama-3.3-70B AWQ (local vLLM) | extracted page text |

GPT-4o appears twice on purpose. The vision model reads page images and the text
model reads extracted text, so a naive three-way comparison measures *pipeline plus
model* and cannot separate them. Running the one model both ways is cheap and makes
the modality contribution measurable instead of assumed.

## Setup

```bash
cp .env.example .env        # then put the real OPENAI_API_KEY in it
./.venv/bin/python run.py --list
```

Drop RFP PDFs into `docs/`. Both `docs/` and `.env` are gitignored.

## Use

```bash
./.venv/bin/python run.py --dry-run                    # page selection, no API calls
./.venv/bin/python run.py -m gpt-4o-text --limit 1     # one model, one document
./.venv/bin/python run.py -m gpt-4o-text -m gpt-4o-vision
./.venv/bin/python run.py -m qwen3-vl-32b              # needs vLLM up on :8000
```

Results land in `results/<backend>/<doc>.json`.

## How it works

**One output contract.** Every model returns the same JSON per field:
`present`, `value`, `page`, `quote`, `confidence`. Enforced by OpenAI strict
structured outputs and by vLLM `guided_json` respectively, so parsing never fails
and grading code never branches on which model answered.

**Evidence is checked mechanically.** Every `present: true` answer must carry a
verbatim `quote`. `rfpbench.document.find_quote` looks for that quote in the source
PDF and classifies the answer:

| status | meaning |
|---|---|
| `verified` | quote found on the cited page |
| `wrong_page` | quote is real but the page citation is wrong |
| `unverified` | quote appears nowhere — fabricated |
| `no_quote` | claimed present, offered no evidence |
| `absent` | model said the RFP does not specify this |

This gives a real quality signal **before any ground truth exists** — `groundedness`
and `hallucination_rate` are computed per document in every result file.

**Fields are asked in 5 clusters**, grouped by where they co-locate in real RFPs
(`rfpbench/fields.py`), so one page selection serves several fields. RFPs run
50–200 pages and a page image costs 1–2k vision tokens; stuffing whole documents is
not an option, and it is what would otherwise make the 4-bit 70B unusable.

**Page selection** (`select_pages`) is keyword scoring over page text, with the
first two pages always pinned — deadlines, contact and submission method live there
far more often than keyword scoring alone would find. Swap it for embeddings if it
proves to be the bottleneck, but measure first.

## Files

```
rfpbench/fields.py     the 17 fields: type, cluster, retrieval keywords, guidance
rfpbench/schema.py     pydantic -> JSON schema, the output contract
rfpbench/document.py   PDF -> pages, page selection, quote verification
rfpbench/backends.py   the three models behind one OpenAI-compatible interface
rfpbench/prompts.py    one prompt template; only modality varies
rfpbench/runner.py     orchestration, evidence checking, per-doc summary
tools/make_sample_rfp.py  synthetic RFP for smoke tests (NOT benchmark data)
```

## Not built yet

- **Ground truth + grading.** No labels exist yet. Field types in `fields.py`
  already encode how each will be graded (exact-match after normalisation for 14 of
  17; set F1 for lists/tables; rubric only for the 2–3 genuinely free-text ones).
- **Local model deployment.** Qwen3-VL-32B and Llama-70B AWQ cannot both fit on one
  48GB A6000 — roughly 20GB and 38GB respectively. Run them in separate passes.
- **OCR.** If the corpus is scanned, the text backends see nothing; `--dry-run`
  flags any PDF with no text layer.

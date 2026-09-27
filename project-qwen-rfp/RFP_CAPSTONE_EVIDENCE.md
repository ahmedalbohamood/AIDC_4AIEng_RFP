# RFP AI Capstone — Evidence File

Generated: 2026-09-22 (inspection performed live against the running system; no project files, deployments, or cluster state were modified to produce this report).

---

## 1. PROJECT INFORMATION

- **Project name:** RFP field-extraction benchmark (`project-qwen-rfp`)
- **Current project path:** `/home/ubuntu/aidc/project-qwen-rfp`
- **Git repository:** NOT VERIFIED — this directory (and its parent `/home/ubuntu/aidc`) is **not a git repository**. `git rev-parse --is-inside-work-tree` returns `fatal: not a git repository (or any parent up to mount point /)`. No `.git` directory exists.
- **Current branch:** NOT VERIFIED (no git repo)
- **Current commit hash:** NOT VERIFIED (no git repo)
- **Git status:** NOT VERIFIED (no git repo)
- **Short description:** A CLI benchmark harness that extracts 17 defined fields from RFP PDFs using multiple LLM backends (2 local vLLM-served open-weight models + several API models), verifies evidence (quote-in-source-page checking), grades against hand-written ground truth, and produces per-field comparison reports.
- **Current implementation status:** Core extraction/benchmark pipeline is mature and has produced real numeric results (see §15). No frontend, backend API server, RAG, agent, or fine-tuning code exists in this project.

### CORE CAPSTONE REQUIREMENTS (status snapshot)
| Item | Status |
|---|---|
| Model deployment (Docker) | COMPLETE (live) |
| Model deployment (Kubernetes) | IN PROGRESS / PENDING (manifest exists, scaled to 0) |
| Model comparison (≥3 models) | COMPLETE (8 backends have results) |
| Benchmark (accuracy/latency/tokens) | COMPLETE (real numbers exist, §15) |
| AI Hub demonstration | NOT VERIFIED / PENDING |

### STRETCH FEATURES (status snapshot)
| Item | Status |
|---|---|
| Frontend application | NOT STARTED |
| Chat | NOT STARTED |
| Agent | NOT STARTED |
| RAG | NOT STARTED |
| Fine-tuning | NOT STARTED |

---

## 2. CAPSTONE REQUIREMENTS

Per the guidance supplied, the required core project is deploy 1 open-weight model (Docker+K8s), compare ≥3 models, use 5 "BeamData" RFPs, extract the 17 fields, compare to ground truth, measure quality/tokens/latency, produce a benchmark report, and demonstrate in AI Hub.

**Important discrepancy found:** No file, filename, or string "BeamData" exists anywhere in `/home/ubuntu/aidc` (confirmed by `grep -ril "beamdata"` returning no matches). The actual dataset in `docs/` is a corpus of real, publicly-sourced RFPs (see §9) — not a set explicitly labeled "BeamData." This is reported as **NOT VERIFIED** rather than assumed equivalent.

The 17-field appendix matches exactly what is implemented in `rfpbench/fields.py` (verified key-by-key in §12).

---

## 3. HARDWARE

```
nvidia-smi:
  GPU: NVIDIA RTX A6000
  Total VRAM: 49140 MiB (~48 GB)
  Used VRAM: 43353 MiB
  Driver Version: 550.90.12
  CUDA Version: 12.4
  Active GPU process: PID 3256087, "VLLM::EngineCore", 43346 MiB

python3 --version: Python 3.10.12   (bare `python` command: NOT FOUND on PATH)
docker --version: Docker version 27.2.1, build 9e34c9b
git --version: git version 2.34.1
kubectl version --client: Client Version v1.36.4+k3s1 (Kustomize v5.8.1)
```

---

## 4. CURRENT MODEL

Identified from the live Docker container `vllm-bench` (`docker inspect`) and a successful `/v1/models` call.

- **Exact model name / Hugging Face identifier:** `QuantTrio/Qwen3-VL-32B-Instruct-AWQ`
- **Parameter size:** 32B (as documented in the model name; not independently re-verified against the HF card)
- **Quantization:** AWQ (per model name / repo; the container's launch args do not pass an explicit `--quantization` flag — see below)
- **Dtype:** NOT VERIFIED from the running container's exact args (no `--dtype` flag present in the live `docker inspect` command — see discrepancy note below)
- **Configured context length:** `--max-model-len 32768` (from live `docker inspect .Config.Cmd`)
- **vLLM version:** v0.29.0 (from image label `ai.vllm.image.tag`, build commit `98dff2a81d747d1dba01a47f939f48c3526d4206`)
- **Docker image:** `vllm/vllm-openai:latest` (resolves to tag `v0.29.0`)
- **Serving command/arguments (verified via `docker inspect`):**
  ```
  vllm serve --model QuantTrio/Qwen3-VL-32B-Instruct-AWQ
             --served-model-name QuantTrio/Qwen3-VL-32B-Instruct-AWQ
             --max-model-len 32768
             --gpu-memory-utilization 0.90
  ```
- **GPU memory utilization setting:** 0.90
- **Vision/multimodal support:** YES — `QuantTrio/Qwen3-VL-32B-Instruct-AWQ` is used as the `vision` modality backend in `rfpbench/backends.py` (reads rendered page images).
- **Current runtime status:** RUNNING — container `vllm-bench` up 11 hours; `/health` returns HTTP 200; `/v1/models` returns the model id.

**Discrepancy note:** the repo's `serve.sh` script's `qwen` preset specifies `--max-model-len 49152`, `--quantization awq_marlin`, `--dtype half`, and `--limit-mm-per-prompt '{"image":24}'`. The **currently running container's actual launch command** (per `docker inspect`) shows only `--max-model-len 32768` and `--gpu-memory-utilization 0.90`, with no explicit `--quantization`, `--dtype`, or `--limit-mm-per-prompt` flags. This means the live container was started with a different command than the script's current preset (possibly an older invocation, or vLLM defaults were relied on for quantization/dtype). Reported as observed, not reconciled — do not assume `serve.sh` reflects the running container exactly.

---

## 5. DOCKER

- **Dockerfile paths:** NOT FOUND in `project-qwen-rfp` (no `Dockerfile*` anywhere in the project tree).
- **Compose files:** NOT FOUND (no `*compose*` file in the project tree).
- **Model serving image:** `vllm/vllm-openai:latest` (`vllm/vllm-openai:v0.29.0`), 21.5 GB.
- **Exposed ports:** container `8000/tcp` → host `8100/tcp` (`0.0.0.0:8100->8000/tcp`).
- **Mounted volumes:** bind mount `/home/ubuntu/hf-cache` → `/root/.cache/huggingface` (RW).
- **GPU configuration:** `--gpus all` (device request: `Driver: "", Count: -1, Capabilities: [["gpu"]]`).
- **Environment variable NAMES only** (values never inspected/printed): `PATH`, `NVARCH`, `NVIDIA_REQUIRE_CUDA`, `NV_CUDA_CUDART_VERSION`, `CUDA_VERSION`, `LD_LIBRARY_PATH`, `NVIDIA_VISIBLE_DEVICES`, `NVIDIA_DRIVER_CAPABILITIES`, `DEBIAN_FRONTEND`, `UV_HTTP_TIMEOUT`, `UV_INDEX_STRATEGY`, `UV_LINK_MODE`, `UV_PYTHON_INSTALL_DIR`, `UV_CACHE_DIR`, `UV_OVERRIDE`, `VLLM_ENABLE_CUDA_COMPATIBILITY`, `TORCH_CUDA_ARCH_LIST`, `VLLM_USAGE_SOURCE`, `VLLM_BUILD_COMMIT`, `VLLM_BUILD_PIPELINE`, `VLLM_BUILD_URL`, `VLLM_IMAGE_TAG`. No API-key or secret-named env vars present on this container.
- **Current container status (relevant containers only):**

| Container | Image | Status |
|---|---|---|
| `vllm-bench` | `vllm/vllm-openai:latest` | Up 11 hours (the live serving container) |
| `funny_noether` | `ahmedhhb/aidc-serving:cpu-v2` | Exited (0) 13 days ago |
| `dcgm-exporter` | `nvcr.io/nvidia/k8s/dcgm-exporter:3.3.9-3.6.1-ubuntu22.04` | Up 12 days (cluster GPU metrics, not project-specific) |
| `node-exporter` | `quay.io/prometheus/node-exporter:v1.8.2` | Up 12 days (cluster metrics, not project-specific) |

Two additional images (`ahmedhhb/aidc-serving:cpu-v2`, `iabdulaziz/aidc-serving:cpu-v1`) exist locally but are **not part of this project's repo** — they belong to other teammates' serving experiments on the shared team pod and are not referenced by any file in `project-qwen-rfp`.

---

## 6. KUBERNETES

```
kubectl get nodes: 1 node (aidc-t04, control-plane, Ready, v1.36.4+k3s1)
```

**Namespaces relevant to this project: `team`** (shared team namespace referenced by the pod README as "the engine on the card" / "the public endpoint").

| Namespace | Deployment | Pods | Replicas | Status |
|---|---|---|---|---|
| team | `vllm` | none currently | **0/0 (scaled to zero)** | Deployment object exists; last successful rollout recorded 2026-09-08→2026-09-10; **not currently serving** |

**Deployment `vllm` spec (namespace `team`), as currently stored in the cluster:**
- Image: `vllm/vllm-openai:v0.27.1`
- Args: `--model=Qwen/Qwen2.5-1.5B-Instruct-AWQ --quantization=awq --dtype=half --max-model-len=4096 --gpu-memory-utilization=0.85 --enable-auto-tool-choice --tool-call-parser=hermes`
- **This is a different, smaller model (Qwen2.5-1.5B-Instruct-AWQ) than the model currently live in Docker (Qwen3-VL-32B-Instruct-AWQ).** The Kubernetes deployment and the Docker deployment are not serving the same model.
- Env: `VLLM_API_KEY` sourced from Secret `serving-keys` key `api-key` (value never read/printed)
- Resources — requests = limits: `cpu: 4`, `memory: 16Gi`, `nvidia.com/gpu: 1`
- Readiness probe: `GET /health:8000`, period 5s, threshold 3
- Startup probe: `GET /health:8000`, period 10s, failureThreshold 60
- Volume: hostPath `/var/lib/hf-cache` → `/root/.cache/huggingface`
- **Replicas: 0 (currently scaled down — not running)**

**Services (namespace `team`):**
| Service | Type | Cluster-IP | Port | Selector | Endpoints |
|---|---|---|---|---|---|
| `team-serving` | NodePort | 10.43.190.66 | 8000 (nodePort 30800) | `app=vllm` | **none** (no backing pod) |
| `vllm-engine` | ClusterIP | 10.43.34.228 | 8000 | `app=vllm` | **none** (no backing pod) |

Per the pod's top-level README, NodePort **30800** is the externally-tunneled "team endpoint" (`https://t04.aidc.nadir.sh`). **This endpoint currently has no backing pod and is not serving traffic.** The only currently-live model endpoint is the Docker container on port 8100 (§4/§7).

Other pods in the cluster (`abdulaziz`, `ahmed`, `faisal`, `default` namespaces — `pod-a`, `pod-b`, `pod-c`, `prober`, `impossible-cpu`, `verify-loadgen-*`, `loadgen`) are unrelated per-person lab exercises on the shared pod, not part of this project.

Cluster infra pods `alert-inbox`, `grafana`, `prometheus`, `health-shim` (namespace `team`) are running and healthy but are shared team monitoring infrastructure, not specific to this RFP project.

**Kubernetes YAML file paths in the repository:** NONE FOUND. No `*.yaml`/`*.yml` manifest exists anywhere under `project-qwen-rfp` (a search found only third-party `node_modules` CI config files under `docx_build/`, unrelated to Kubernetes). The `team/vllm` Deployment currently in the cluster was applied via `kubectl apply` with an inline JSON body (visible in its `kubectl.kubernetes.io/last-applied-configuration` annotation) — its source manifest, if one exists, is **not present in this project directory**.

No Kubernetes resources were modified during this inspection.

---

## 7. MODEL ENDPOINT

Tested only non-destructive read endpoints.

| Endpoint | Result |
|---|---|
| `GET http://localhost:8100/health` | **HTTP 200** |
| `GET http://localhost:8100/v1/models` | **HTTP 200**, returns `{"id":"QuantTrio/Qwen3-VL-32B-Instruct-AWQ", ...}` |

- **Endpoint status:** UP
- **Model ID returned:** `QuantTrio/Qwen3-VL-32B-Instruct-AWQ`
- **Authentication required:** NO — this container has no `VLLM_API_KEY` set (confirmed: no such env var name in `docker inspect`'s env list), so the endpoint is open on the local port. No key was used or exposed in testing.

The Kubernetes-fronted endpoint (NodePort 30800 / `team-serving`) is currently unreachable (no backing pod — §6).

---

## 8. MODEL REQUEST

One minimal, non-benchmark test request was sent directly to the live endpoint (`http://localhost:8100/v1/chat/completions`), asking the model to reply with a single word — not a BeamData/benchmark RFP document.

- **Model:** `QuantTrio/Qwen3-VL-32B-Instruct-AWQ`
- **Request succeeded:** YES
- **HTTP status:** 200
- **Latency:** ≈0.09 s (trivial prompt, 15 prompt tokens)
- **Token usage:** `prompt_tokens=15, completion_tokens=2, total_tokens=17`

---

## 9. DATASET INVENTORY

Directory: `docs/` (20 PDF files total, no DOCX/TXT source RFPs).

- **Numbered "final-style" RFPs (8):** `01_Reference_Data_Management_Services_RFP.pdf`, `02_Certification_Testing_Platform_and_Services_RFP.pdf`, `03_Asset_Management_GIS_IT_Consulting_RFP.pdf`, `04_Data_Centre_Download_Integration_Services_RFP.pdf`, `05_SharePoint_Migration_and_Road_Map_RFP.pdf`, `06_Data_and_Analytics_Cloud_Solution_NRFP.pdf`, `07_Student_Global_Payment_System_RFP.pdf`, `08_High_Availability_SQL_Database_Solution_RFP.pdf`
- **Additional named real-world RFPs (11):** `AB-2025-02456-RFP #25-004ERP Requirements Analysis and Readiness Review_Final (1).pdf`, `AB-2026-05648-197-2027 RFP Learning Management System (LMS) Platform  Support (2).pdf`, `City of Medicine Hat - LMS tender.pdf`, `EN_-_ERP_RFP_24.25.04.pdf`, `RFP CP-730126 Generative AI RFP (4).pdf`, `RFP-2026-7-PR-EGYPTDUEDILIGENCE.pdf`, `RFP-2026-8-PR-CASCADE-Updated-with-QAs-1.pdf`, `RFP-2026-9-DE-MIDDLEWARE-V2-1.pdf`, `RFP_clean_for_model (1).pdf`, `RFP_clean_for_model.pdf`, `Shafter_RFP_Final_201802011144290034.pdf`
- **Synthetic smoke-test doc (1):** `sample-rfp-synthetic.pdf` — explicitly documented in the README as "NOT benchmark data."
- **Formats:** 100% PDF. No DOCX/TXT source RFPs found.
- **"5 BeamData RFPs" as a named set:** NOT VERIFIED — no such label exists anywhere in the project.

**Ground truth files** (`ground_truth/*.json`, 11 total): one JSON per RFP above, covering **10 real RFPs + the synthetic sample**. (Full list in §10.)

**Annotation files:** the ground-truth JSON files themselves are the annotation artifacts (see §10 for schema).

**Training / validation / test data splits:** NOT FOUND. There is no train/val/test split; ground truth exists per-document and grading (`grade.py`) runs over whichever documents have ground truth. Full RFP document contents are not reproduced in this report per instructions.

---

## 10. GROUND TRUTH

- **Exists:** YES — `ground_truth/*.json`, 11 files.
- **RFPs with completed ground truth (11):**
  `01_Reference_Data_Management_Services_RFP`, `02_Certification_Testing_Platform_and_Services_RFP`, `03_Asset_Management_GIS_IT_Consulting_RFP`, `04_Data_Centre_Download_Integration_Services_RFP`, `AB-2025-02456-RFP #25-004ERP Requirements Analysis and Readiness Review_Final (1)`, `AB-2026-05648-197-2027 RFP Learning Management System (LMS) Platform  Support (2)`, `City of Medicine Hat - LMS tender`, `EN_-_ERP_RFP_24.25.04`, `RFP CP-730126 Generative AI RFP (4)`, `RFP-2026-8-PR-CASCADE-Updated-with-QAs-1`, `sample-rfp-synthetic` (synthetic, not benchmark data).
  **9 of 20 docs in `docs/` still have no ground truth** (`05`, `06`, `07`, `08`, `RFP-2026-7-PR-EGYPTDUEDILIGENCE`, `RFP-2026-9-DE-MIDDLEWARE-V2-1`, `RFP_clean_for_model (1)`, `RFP_clean_for_model`, `Shafter_RFP_Final_...`) — PENDING.
- **Fields annotated per document:** 17 of 17 (all documents fully annotated across all fields; verified directly by counting keys in each JSON).
- **Schema used:** `{"doc_id": str, "annotator": str, "fields": {<17 field keys>: {"present": bool, "value": ..., "difficulty": "easy"|"medium"|"hard", "note": str}}}`.
- **Present/absent handling:** explicit boolean `present` per field; `value` is null/empty when absent.
- **Evidence/page handling:** ground truth does not itself carry a `page`/`quote` pair — evidence-grounding for page/quote is checked separately, mechanically, against model *answers* (`rfpbench/document.find_quote`), independent of ground truth.
- **Annotation status:** COMPLETE for the 11 files listed above.
- **Human validation status:** NOT VERIFIED. The `annotator` field in every ground-truth file identifies the annotator as an LLM ("claude" / "claude-sonnet-5") that read the full source PDF directly and wrote the answers, e.g.: *"claude (read all 57 pages directly, 2026-09-20, AFTER freezing claude-opus-5-text extraction to keep the test blind)"*. No separate human sign-off or independent human review of these ground-truth files was found in the repository. Do not claim human-validated ground truth.

---

## 11. BACKEND

**No web backend / API server exists in this project.** This is a CLI-only benchmark harness (`run.py`, `grade.py`, `report.py`, `rescore.py` invoked directly via `./.venv/bin/python`). A search for `FastAPI`/`uvicorn`/`fastapi` anywhere under `project-qwen-rfp` returned no matches.

Pipeline stages actually implemented, all as library code called from `run.py`/`grade.py` (not exposed via any HTTP API):

| Stage | Status | Implementation |
|---|---|---|
| Upload | NOT IMPLEMENTED | PDFs are placed directly into `docs/` on disk; no upload endpoint |
| Storage | Local filesystem only | `docs/` (source), `results/` (extraction outputs), `ground_truth/` |
| Processing / PDF parsing | COMPLETE | PyMuPDF (`pymupdf`), optional Docling (`--docling` flag, cached to `.docling_cache/`) |
| DOCX/TXT parsing | NOT IMPLEMENTED | corpus is 100% PDF |
| Page-aware chunking | COMPLETE | `select_pages()` in `rfpbench/document.py` — keyword-scored candidate pages per field cluster, first 2 pages always pinned |
| Model request | COMPLETE | `rfpbench/backends.py` — single OpenAI-compatible call path for both API and local vLLM models |
| 17-field extraction | COMPLETE | `rfpbench/runner.py` + `rfpbench/schema.py` |
| Pydantic validation | COMPLETE | `rfpbench/schema.py` (`pydantic` `BaseModel`, `extra="forbid"`, strict JSON schema) |
| Evidence validation | COMPLETE | mechanical quote-in-page verification (`verified`/`wrong_page`/`unverified`/`no_quote`/`absent`) |
| Result persistence | COMPLETE | JSON files under `results/<backend>/<doc_id>.json` |
| Result retrieval | COMPLETE (file read only) | `grade.py`/`report.py` read saved JSON directly; no API |

**Implemented backend API endpoints:** NONE. There is no HTTP server in this project.

- **Parser libraries:** `pymupdf` (PyMuPDF), optional `docling`
- **Upload storage location:** N/A (manual file placement in `docs/`)
- **Processed document storage:** `.docling_cache/` (cached Docling extraction), `.embedding_cache.json` (cached embeddings for semantic grading experiment), `.judge_cache.json` (cached LLM-judge grading calls)
- **Extraction storage:** `results/<backend>/<doc_id>.json`
- **OCR status:** DISABLED BY DESIGN — `rfpbench/document.py` sets `opts.do_ocr = False` with the comment "every doc in this corpus has a real text layer." `--dry-run` flags any PDF lacking a text layer, but no OCR fallback is implemented.
- **Language detection status:** NOT IMPLEMENTED — no reference to language detection found anywhere in the codebase.

---

## 12. EXTRACTION IMPLEMENTATION

All 17 machine-readable keys were verified directly against `rfpbench/fields.py` (`FIELDS` tuple) — **exact match, all present, correct numbering 1–17:**

```
1  submission_deadline
2  questions_deadline
3  rfp_contact
4  submission_method
5  contract_term
6  scope_of_deliverables
7  mandatory_submission_requirements
8  mandatory_technical_requirements
9  evaluation_criteria
10 minimum_score_threshold
11 pricing_structure
12 insurance_requirements
13 vendor_experience_required
14 references_required
15 data_security_requirements
16 data_hosting_residency
17 vendor_demonstration_required
```

- **Schema source file:** `rfpbench/fields.py` (field definitions), `rfpbench/schema.py` (Pydantic → JSON-schema output contract)
- **Extraction service file:** `rfpbench/runner.py` (orchestration), `rfpbench/backends.py` (model call layer)
- **Prompt file:** `rfpbench/prompts.py` — one shared template; only modality (text vs. vision) varies
- **Extraction prompt version:** NOT VERIFIED — no explicit version string/tag found in `prompts.py`
- **Confidence values:** every field answer carries a `confidence: float` (0.0–1.0), self-reported by the model, per `rfpbench/schema.py`
- **Evidence structure:** `{present: bool, value, page: Optional[int], quote: Optional[str], confidence: float}` — one shape shared by all backends
- **Conflict structure:** NOT FOUND as a distinct field/mechanism — the closest equivalent is the mechanical evidence classification (`verified`/`wrong_page`/`unverified`/`no_quote`/`absent`), which flags fabricated or misplaced citations but does not model multi-source "conflicts" as a first-class structure
- **Malformed JSON retry behavior:** COMPLETE and documented — `Backend.call()` retries once at `temperature=0.3` on an unparseable-JSON error (root cause: observed infinite whitespace-repetition loop under guided decoding on some vLLM models); if both attempts fail, a partial-JSON salvage routine (`_salvage_partial_json`) recovers whichever top-level fields did complete rather than discarding the whole cluster.

---

## 13. TESTS

**No automated test suite exists.** A search for `test_*.py` / `*_test.py` anywhere under `project-qwen-rfp` returned no results.

- **Exact test command:** N/A — no test command exists to run
- **Passed / Failed / Skipped / Warnings:** N/A
- **Functionality covered:** NONE — PENDING

This is reported as-is per instructions ("If something has not been completed, write: PENDING"): **automated test suite: PENDING.**

---

## 14. LIVE RFP EXTRACTION

Evidence of completed real extractions exists abundantly in `results/`. Example, drawn directly from a saved result file (`results/gpt-4o-text/01_Reference_Data_Management_Services_RFP.json`) without altering it:

- **Practice RFP filename:** `01_Reference_Data_Management_Services_RFP.pdf`
- **Document ID:** `01_Reference_Data_Management_Services_RFP`
- **Page count:** recorded in the result file (`n_pages`); this document is also independently confirmed as 57 pages in the ground-truth annotator's note (§10)
- **Model:** `gpt-4o` (backend key `gpt-4o-text`)
- **Prompt version:** NOT VERIFIED (no version tag emitted into result files)
- **Number of chunks:** 5 field clusters (per `rfpbench/fields.py` `CLUSTERS`)
- **Latency:** 30.92 s (`totals.latency_s`)
- **Input tokens:** 30,966 (`totals.prompt_tokens`)
- **Output tokens:** 2,686 (`totals.completion_tokens`)
- **Total tokens:** 33,652
- **Retries:** `totals.errors = 0` for this run (retry mechanism exists in code — §12 — but was not triggered for this specific result)
- **Schema validation errors:** 0 (all 17 fields returned, well-formed)
- **Evidence validation:** `{verified: 13, wrong_page: 3, unverified: 0, no_quote: 0, absent: 1}`, groundedness 1.0, hallucination_rate 0.0
- **Saved result paths:** `results/gpt-4o-text/01_Reference_Data_Management_Services_RFP.json` (and equivalently one JSON file per backend/document — 8 backend directories, up to 20 documents each; full list in §15/§9)

This satisfies the "completed real live extraction" bar; therefore the PENDING sentinel is **not** used for this section.

---

## 15. BENCHMARK

Benchmark artifacts inspected: `reports/01_Reference_Data_Management_Services_RFP_comparison.md` (one detailed per-field comparison report, 3 models), and the full `results/` corpus graded live against `ground_truth/` by running the project's own `grade.py` (read-only; uses its on-disk judge/embedding caches, no files modified).

| Item | Status |
|---|---|
| 5 final BeamData RFPs | NOT VERIFIED (no "BeamData" label exists; see §2/§9) — **actual corpus used: 10 real RFPs + 1 synthetic have ground truth, out of 20 total in `docs/`** |
| Ground Truth | COMPLETE for 11 documents (§10) |
| Model 1 output (gpt-4o-text) | COMPLETE — 11 GT documents graded |
| Model 2 output (qwen3-vl-32b-vision, the deployed open-weight model) | COMPLETE — 9 GT documents graded |
| Model 3 output (additional models) | COMPLETE — llama-70b-text (8 docs), qwen3.5-9b-text (11 docs), k2-horizon-7b-text (11 docs), gpt-5.5-vision (2 docs), claude-opus-5-text (1 doc), claude-sonnet-5-text (1 doc) all have graded results |
| Correct / Partial / Wrong / Missing field counts | COMPLETE — exact numbers below |
| Hallucination counts | Tracked per-document as `hallucination_rate` in each result file (not separately aggregated here; see §14 example) |
| Accuracy metric | COMPLETE — exact numbers below |
| Token usage | COMPLETE — recorded per document per backend in `totals.prompt_tokens`/`totals.completion_tokens` |
| Latency | COMPLETE — recorded per document per backend in `totals.latency_s` |
| Model comparison table | COMPLETE (below), plus a full field-by-field narrative report for one document (`reports/`) |
| Benchmark conclusions | PARTIAL — the one written narrative report covers only 1 of the 11 graded documents; no cross-document written conclusions document exists |

### Actual numeric results (from `grade.py`, run live against current `results/` + `ground_truth/`)

**Overall accuracy by backend:**

| Backend | Correct | Partial | Wrong | Missing | Total fields graded | Accuracy |
|---|---:|---:|---:|---:|---:|---:|
| claude-opus-5-text | 15 | 1 | 1 | 0 | 17 | 88.2% |
| claude-sonnet-5-text | 16 | 1 | 0 | 0 | 17 | 94.1% |
| gpt-4o-text | 107 | 48 | 32 | 0 | 187 | 57.2% |
| gpt-5.5-vision | 26 | 8 | 0 | 0 | 34 | 76.5% |
| k2-horizon-7b-text | 118 | 43 | 24 | 2 | 187 | 63.1% |
| llama-70b-text | 71 | 40 | 25 | 0 | 136 | 52.2% |
| qwen3-vl-32b-vision | 100 | 34 | 16 | 3 | 153 | 65.4% |
| qwen3.5-9b-text | 114 | 46 | 27 | 0 | 187 | 61.0% |

Note on sample sizes: `claude-opus-5-text`, `claude-sonnet-5-text`, and `gpt-5.5-vision` were run on only 1, 1, and 2 documents respectively (used to *produce* ground truth in a blind test-then-freeze process per the annotator notes in §10, or as a late exploratory add — see `rfpbench/backends.py` comment for `gpt-5.5-vision`, dated 2026-09-21). Their accuracy figures are **not directly comparable** to the other backends, which were graded across 8–11 documents. `gpt-4o-vision` is registered in code but has **no saved results** — PENDING for that specific modality.

**Accuracy by difficulty (excerpt; full table available via `grade.py` output):**

| Backend | Easy | Hard | Medium |
|---|---:|---:|---:|
| gpt-4o-text | 87.0% | 40.0% | 39.7% |
| k2-horizon-7b-text | 87.0% | 45.5% | 52.4% |
| llama-70b-text | 75.0% | 37.5% | 41.7% |
| qwen3-vl-32b-vision | 86.2% | 51.2% | 53.8% |
| qwen3.5-9b-text | 82.6% | 49.1% | 47.6% |

All backends score highest on "easy" fields and drop substantially on "hard" fields (deliberate traps in ground truth — see §10 annotator notes, e.g. conflicting timezones).

---

## 16. MODEL SELECTION

| Slot | Model | Status |
|---|---|---|
| Model 1 — OpenAI model | `gpt-4o` (backend keys `gpt-4o-text`, `gpt-4o-vision`) | **CONFIRMED** (gpt-4o-text has full graded results; gpt-4o-vision is registered but has no saved run — CANDIDATE only for the vision variant) |
| Model 2 — Deployed open-weight model | `QuantTrio/Qwen3-VL-32B-Instruct-AWQ` (backend key `qwen3-vl-32b`) | **CONFIRMED** — currently live in Docker (§4/§7), graded on 9 documents |
| Model 3 — Additional comparison model | `casperhansen/llama-3.3-70b-instruct-awq` (`llama-70b`), `QuantTrio/Qwen3.5-9B-AWQ` (`qwen3.5-9b`), `IFM/K2-Horizon-7B` (`k2-horizon-7b`) | **CONFIRMED** (all three have full graded results; the requirement of ≥3 total models is exceeded) |

Additional backends present with results but outside the minimal-3 requirement: `gpt-5.5` (vision), `claude-opus-5`, `claude-sonnet-5` (used for ground-truth generation, see §10).

---

## 17. FRONTEND

**No frontend application exists in this project.** No `package.json`/web-framework project for a UI was found under `project-qwen-rfp` other than `docx_build/` (a Node.js script that builds a `.docx` benchmark write-up and a PDF explainer — a documentation build tool, not an application).

| Item | Status |
|---|---|
| Extract page | NOT STARTED |
| 17-field results (UI) | NOT STARTED |
| Evidence viewer | NOT STARTED |
| Confidence/status (UI) | NOT STARTED |
| Arabic | NOT VERIFIED |
| English | NOT VERIFIED |
| RTL | NOT VERIFIED |
| Dark mode | NOT VERIFIED |
| Chat (STRETCH) | NOT STARTED |
| RFP Review Agent (STRETCH) | NOT STARTED |

All results in this project are currently consumed via CLI output and raw JSON/Markdown files, not a UI.

---

## 18. FINE-TUNING / RAG / AGENT

None of these are required core deliverables; reported here purely as observed state.

| Item | Status |
|---|---|
| Fine-tuning | NOT STARTED — no training scripts, datasets, or checkpoints found |
| LoRA / QLoRA | NOT STARTED |
| RAG | NOT STARTED — no vector database or retrieval-augmented generation pipeline exists |
| Embeddings | IN PROGRESS (narrow scope) — `rfpbench/semantic.py` implements embedding-based *similarity scoring for grading free-text answers* (an alternative to fuzzy string match), cached in `.embedding_cache.json`. This is **not** a retrieval pipeline for extraction and should not be conflated with RAG. |
| Vector DB | NOT STARTED — no vector database (e.g., FAISS, Chroma, pgvector) found anywhere in the project |
| Agent implementation | NOT STARTED |

---

## 19. AI HUB

No reference to "AI Hub" (or variants: `aihub`, `ai_hub`) was found anywhere in `/home/ubuntu/aidc` (project or shared pod files).

- **Model integrated into AI Hub:** NOT VERIFIED
- **Model visible in playground:** NOT VERIFIED
- **Successful interaction (via AI Hub):** NOT VERIFIED
- **Demo completed:** NOT STARTED

The closest existing infrastructure for an external demo is the team's Kubernetes NodePort 30800 (`team-serving`, tunneled to `https://t04.aidc.nadir.sh` per the pod README) — but as documented in §6, that service currently has **no backing pod** and is not reachable. The only currently reachable model endpoint is the local Docker port 8100, which is not exposed externally.

**AI Hub demonstration: PENDING.**

---

## 20. CURRENT CAPSTONE CHECKLIST

| Requirement | Status | Evidence |
|---|---|---|
| Kickoff | NOT VERIFIED | No kickoff/planning document found in the project |
| Requirements | COMPLETE | 17-field schema fully implemented and matches the specified appendix (§12) |
| Model selection | COMPLETE | 8 backends registered/run; ≥3-model minimum exceeded (§16) |
| Docker deployment | COMPLETE | `vllm-bench` container live, `/health` 200, model served (§4, §7) |
| Kubernetes deployment | IN PROGRESS | `team/vllm` Deployment manifest exists in-cluster but scaled to 0/0, not currently serving (§6) |
| Live model endpoint | COMPLETE | Docker-hosted endpoint responds on port 8100 (§7) |
| Successful model request | COMPLETE | Minimal live test call succeeded, HTTP 200 (§8) |
| 5-RFP dataset | NOT VERIFIED | No "BeamData"-labeled 5-RFP set found; actual corpus is 20 PDFs, 11 with ground truth (§9) |
| 17-field schema | COMPLETE | Verified key-for-key against `rfpbench/fields.py` (§12) |
| Ground Truth | COMPLETE (for 11 of 20 docs) | `ground_truth/*.json`, LLM-annotated, no independent human validation found (§10) |
| Evaluation dataset | IN PROGRESS | 11 of 20 documents have ground truth; 9 remain unannotated |
| Three-model benchmark | COMPLETE | 8 backends graded with real accuracy numbers (§15) |
| Accuracy measurement | COMPLETE | Exact per-backend accuracy table produced by `grade.py` (§15) |
| Token measurement | COMPLETE | Recorded per document per backend in result JSON (`totals.prompt_tokens`/`completion_tokens`) |
| Latency measurement | COMPLETE | Recorded per document per backend (`totals.latency_s`) |
| Model comparison | COMPLETE | Aggregate table (§15) + detailed field-level report for 1 document (`reports/`) |
| Benchmark report | IN PROGRESS | One detailed comparison report exists for 1 of 11 documents; no cross-corpus written report exists yet |
| AI Hub | PENDING | No evidence found anywhere in the project or pod (§19) |
| Final presentation | NOT VERIFIED | No presentation artifact found in the project |

---

## 21. IMPORTANT FILES

| Path | Purpose |
|---|---|
| `run.py` | Benchmark CLI entrypoint — runs selected/all backends over `docs/`, saves results |
| `grade.py` | Grades saved results against `ground_truth/`, prints accuracy tables |
| `report.py` | Cross-model summary/disagreement reporting over saved results |
| `rescore.py` | Re-runs evidence (quote) verification over saved results without re-calling models |
| `rfpbench/fields.py` | The 17 field definitions (type, cluster, keywords, guidance) |
| `rfpbench/schema.py` | Pydantic → JSON-schema output contract (the extraction schema) |
| `rfpbench/prompts.py` | The shared extraction prompt template |
| `rfpbench/backends.py` | Model backend registry (GPT-4o, Qwen3-VL-32B, Llama-3.3-70B-AWQ, Qwen3.5-9B, K2-Horizon-7B, GPT-5.5) |
| `rfpbench/document.py` | PDF loading, page selection, quote verification (evidence checking) |
| `rfpbench/runner.py` | Orchestration: calls backend, checks evidence, summarises per document |
| `rfpbench/judge.py` | LLM-as-judge grading for free-text fields (cached in `.judge_cache.json`) |
| `rfpbench/semantic.py` | Embedding-similarity grading experiment (cached in `.embedding_cache.json`) |
| `ground_truth/*.json` | Hand/LLM-written ground truth, 11 files, 17 fields each |
| `results/*/*.json` | Raw per-document, per-backend extraction outputs (8 backend directories) |
| `reports/01_Reference_Data_Management_Services_RFP_comparison.md` | The one existing detailed field-by-field, model-vs-ground-truth write-up |
| `docs/*.pdf` | Source RFP corpus (20 PDFs) |
| `serve.sh` | Script to launch either local vLLM model (`qwen`/`llama`) via Docker |
| `README.md` (project) | Project overview, setup, and architecture notes (partially stale — its "Not built yet" section predates ground truth/grading, which now exist) |
| `docx_build/` | Node.js build scripts producing `RFP-Benchmark-Questions-and-Results.docx` and `Kid-Friendly-Pipeline-Explainer.pdf` (documentation deliverables, not core pipeline) |
| `/home/ubuntu/aidc/README.md` | Shared team-pod environment/infrastructure documentation (namespaces, GPU, tunnel ports) |

No screenshots or live-test artifact files (e.g., recorded UI sessions) were found anywhere in the project.

---

## 22. BLOCKERS

**HIGH PRIORITY**
- Kubernetes deployment for the model is currently scaled to 0 replicas and its backing services have no endpoints — the core "deploy via Kubernetes" requirement is not currently demonstrable live, and it targets a different model (Qwen2.5-1.5B) than the one actually benchmarked/live in Docker (Qwen3-VL-32B).
- No AI Hub integration or demonstration evidence exists anywhere in the project or shared pod.
- Ground truth covers 11 of 20 documents in `docs/`; the "5 BeamData RFPs" as a named, contractually-specified set could not be verified to exist at all.
- No automated test suite exists.

**MEDIUM PRIORITY**
- No cross-corpus written benchmark report exists — only one document has a detailed narrative comparison; the rest of the benchmark evidence exists only as raw numbers from `grade.py`.
- `gpt-4o-vision` is registered as a backend but has no saved results, leaving the "modality confound" comparison the README describes as the project's own stated design goal incomplete.
- Kubernetes manifests for the model deployment are not tracked as files in this repository (applied via ad hoc `kubectl apply`), so the "Kubernetes YAML in repo" evidence trail is missing.
- The running Docker container's actual launch flags differ from `serve.sh`'s current `qwen` preset (missing `--quantization`, `--dtype`, `--limit-mm-per-prompt`), suggesting the live container predates the current script version.

**STRETCH ONLY**
- No frontend, chat, agent, RAG, or fine-tuning work has been started.
- Arabic/English/RTL/dark-mode UI status cannot be assessed since no UI exists.

---

## 23. FINAL SUMMARY

**Project status:**
A mature CLI-based RFP field-extraction benchmark with real, verifiable results across 8 model backends. No web application, backend API, or Kubernetes-served-live model currently exists; the only live, testable model endpoint runs directly via Docker.

**Core requirements complete:**
17-field schema and extraction implementation; Docker-based model deployment (live, tested); comparison across far more than the required 3 models (8 backends with saved results); accuracy, token, and latency measurement, all with real numeric values; a functioning evidence-verification (anti-hallucination) mechanism.

**Core requirements in progress:**
Ground truth and evaluation dataset (11 of 20 documents annotated); a cross-corpus written benchmark report (only 1 of 11 graded documents has a detailed narrative write-up).

**Core requirements remaining:**
A live, currently-running Kubernetes deployment of the benchmarked model (present manifest is scaled to 0 and targets a different, smaller model); AI Hub integration and demonstration (no evidence found at all); a "5 BeamData RFP" dataset as specifically named (could not be verified to exist — a different, larger real-world RFP corpus is in use instead).

**Confirmed deployed model:**
`QuantTrio/Qwen3-VL-32B-Instruct-AWQ`, served via Docker + vLLM v0.29.0 on port 8100, verified live via `/health` and a successful test completion.

**Models selected for benchmark:**
`gpt-4o` (Model 1, OpenAI), `QuantTrio/Qwen3-VL-32B-Instruct-AWQ` (Model 2, deployed open-weight), plus `casperhansen/llama-3.3-70b-instruct-awq`, `QuantTrio/Qwen3.5-9B-AWQ`, and `IFM/K2-Horizon-7B` (Model 3 and beyond) — all CONFIRMED with real graded results.

**Evaluation dataset status:**
IN PROGRESS — 11 of 20 corpus documents have complete, LLM-authored (not independently human-validated) ground truth across all 17 fields.

**Benchmark status:**
COMPLETE at the numeric level (real accuracy/token/latency figures exist for 8 backends); IN PROGRESS at the narrative-report level (only 1 document has a full write-up).

**AI Hub status:**
PENDING — no evidence found anywhere in the project or the shared team pod.

**Stretch work status:**
NOT STARTED across frontend, chat, agent, RAG, and fine-tuning. A narrow embedding-similarity experiment exists for judge/grading purposes only and should not be counted as RAG.

**Biggest remaining blocker:**
There is currently no live, running Kubernetes deployment of the benchmarked model, and no verifiable AI Hub integration exists — both are core requirements and neither is currently demonstrable end-to-end.

---

FILE CREATED:
/home/ubuntu/aidc/project-qwen-rfp/RFP_CAPSTONE_EVIDENCE.md

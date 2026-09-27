# Application / Demo Status

Derived from reading actual source files (`server.py`, `frontend_evidence/src/*`),
not from slides or descriptions. File paths below are inside this materials
package unless noted.

| Component | Status | Evidence |
|---|---|---|
| FastAPI backend | **IMPLEMENTED** | `code/server.py` — real `FastAPI(title="AI RFP System Interface API")` app with CORS middleware, running endpoints (see below). Confirmed live in Kubernetes (`ahmed/rfp-backend`, `ahmed/rfp-combined`) — see `DEPLOYMENT_EVIDENCE.md`. |
| React/Vite frontend | **IMPLEMENTED** | `frontend_evidence/src/App.tsx` (1280 lines), `api.ts`, React 19 + Vite 8 + Tailwind 4 (`frontend_evidence/package.json`). Confirmed live in Kubernetes (`ahmed/rfp-frontend`). |
| Extract workflow | **IMPLEMENTED** | Backend: `POST /documents` (upload, `server.py:92`), `GET /documents/{id}/status` (`:130`), `GET /documents/{id}/fields` (`:249`) — returns all 17 fields per document, backed by `rfpbench.runner.run_document`. Frontend: `api.ts` calls all three endpoints (`uploadDocuments`, `getStatus`, `getFields`). Extraction model is fixed to `k2-horizon-7b` (`server.py:39`, comment: *"the model this project's benchmark picked"*). |
| Chat workflow | **IMPLEMENTED** | Backend: `POST /chat` (`server.py:451`), using hybrid keyword+embedding retrieval (`_retrieve()`, `server.py:419`) against the uploaded document, answered via OpenAI per the module docstring (*"Chat/RAG stays on OpenAI per instruction"*). Frontend: `api.ts` wires a `chat()` call. |
| Agent Review | **IMPLEMENTED** | Backend: `POST /documents/{id}/review` (`server.py:383`), `_run_agent_review()` (`:333`) reads the whole document in one call with a larger token budget (6144 vs. the 3072 used for the 17-field extraction clusters) and a dedicated schema (`_agent_schema()`, `:327`). Frontend: `api.ts` wires a `runAgentReview()` call. |
| AI Hub integration | **NOT FOUND** | A recursive, case-insensitive search for "ai hub" / "aihub" / "ai_hub" across `project-qwen-rfp` and `AI RFP System Interface (1)` returns no hits (only self-referential mentions inside this project's own prior evidence file, `RFP_CAPSTONE_EVIDENCE.md`, which itself reported the same NOT FOUND result on 2026-09-22). No external playground URL, AI-Hub config, or demo-mode flag was found. All Kubernetes Services for this app are `ClusterIP`-only (no NodePort/Ingress), so there is currently no externally reachable URL to demonstrate in an AI Hub either. |
| Prometheus | **IMPLEMENTED / CONFIGURED, LIVE** | `deployment/k8s_ahmed_live/deploy-prometheus.yaml` — `prom/prometheus:v2.55.1`, 1/1 running in `ahmed`. Backend additionally self-instruments: `server.py` imports `prometheus_fastapi_instrumentator` and exposes `GET /metrics` (`server.py:48`, request counts + latency histograms) — this is real applied instrumentation, not just a deployed Prometheus binary with nothing to scrape. |
| Grafana | **CONFIGURED, LIVE — dashboards NOT VERIFIED** | `deployment/k8s_ahmed_live/deploy-grafana.yaml` — `grafana/grafana:11.4.0`, 1/1 running, wired to a `grafana-datasource` ConfigMap pointing at the in-namespace Prometheus. Whether any dashboard has actually been built/imported (vs. a stock empty Grafana install) was **not verified** — this collection did not access the Grafana UI/API to enumerate dashboards. |

## Supporting details confirmed by reading the frontend source

- **Arabic / English (i18n):** `frontend_evidence/src/i18n.ts` defines full `en` and
  `ar` string tables (`translations: Record<Lang, Strings> = { en, ar }`) —
  **IMPLEMENTED**, not just a language toggle stub.
- **RTL:** `App.tsx` sets `direction: isRtl ? 'rtl' : 'ltr'` at 7 distinct
  locations (drag-drop panel, evidence panel, field table header/rows, chat
  panel, page shell, search input) — **IMPLEMENTED**, applied consistently
  across the layout, not a single top-level wrapper only.
- **Dark mode:** `App.tsx` computes a full dark/light token palette (`tk(dark)`)
  from either an explicit user setting or `prefers-color-scheme: dark` — **IMPLEMENTED**.
- **Evidence/status UI:** `types.ts` and the field-table rendering in `App.tsx`
  carry per-field status/confidence — consistent with the backend's
  `present`/`confidence`/`_evidence.status` contract (see `BENCHMARK_METHOD.md`
  §3/§5) being surfaced in the UI, not just used internally.

## Not claimed here

This file does not attempt to verify runtime correctness of the chat, extract, or
review workflows (e.g. by actually calling the live endpoints), per the task's
instruction not to modify or exercise the running system. Everything above is
**implementation status from source code and confirmed live Kubernetes pods**,
not a functional/UX test.

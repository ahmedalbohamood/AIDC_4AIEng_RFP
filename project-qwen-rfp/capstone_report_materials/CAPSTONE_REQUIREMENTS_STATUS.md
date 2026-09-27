# Capstone Requirements Cross-Check

Status values: **DONE** / **PARTIAL** / **NOT VERIFIED** / **NOT DONE**.
Each row cites the evidence file/path inside this materials package.

| Requirement | Status | Evidence |
|---|---|---|
| One open-weight model deployed in Docker | **PARTIAL** — historically done and live-verified on 2026-09-22 (Qwen3-VL-32B-AWQ via `serve.sh`), but no plain-Docker model container is running right now; the GPU today is used by the Kubernetes deployment instead | `DEPLOYMENT_EVIDENCE.md` "CURRENT STATE" vs "HISTORICAL" sections; `deployment/serve.sh` |
| Open-weight model pushed/deployed to Kubernetes | **DONE** — `k2-vllm` Deployment (`IFM/K2-Horizon-7B`), 1/1 available, GPU use cross-confirmed live via `nvidia-smi` + `crictl ps` | `deployment/k8s_ahmed_live/deploy-k2-vllm.yaml`, `capstone_environment.txt` |
| At least three models compared | **PARTIAL** — 8 backends have some graded results across the project's history, exceeding 3, but **on the final identical 5-RFP V2 benchmark only 2 models have complete graded runs** (Lift, Qwen3.5-9B); a 3rd (Qwen3-VL-32B) is only 2/5 done and ungraded; GPT/K2-Horizon/Llama-70B were never run on this final set at all | `FINAL_BENCHMARK_FACTS.md` Section A |
| Five RFP documents | **DONE** — exactly 5 PDFs, hashes recorded | `RFP_FILES.txt`, `rfps/` |
| 17 final extraction fields | **DONE** — verified key-for-key against source | `BENCHMARK_METHOD.md` §1, `code/rfpbench_full/fields.py` |
| Ground Truth | **DONE** — `ground_truth_5_rfps_combined_V2.json`, split per-doc, sha256-pinned in the benchmark's own run manifest | `ground_truth/`, `benchmarks/benchmark_5rfp_v2/run_manifest*.json` |
| Extraction accuracy | **DONE** for Lift and Qwen3.5-9B (exact numbers exist); **NOT DONE** for Qwen3-VL-32B on this set; **NOT DONE** for GPT/K2-Horizon/Llama-70B on this set | `FINAL_BENCHMARK_FACTS.md` |
| Token usage | **DONE** — recorded per-model aggregate for Lift/Qwen3.5-9B on the final set; per-document per-backend for the older 11-doc corpus | `benchmarks/benchmark_5rfp_v2/benchmark_summary*.json`; `benchmarks/results_all_models/*/*.json` |
| Latency | **DONE** — average + median seconds per model on the final set; per-document latency for the older corpus | same as above |
| Benchmark report | **PARTIAL** — two narrative Markdown reports exist for the final 5-RFP V2 set (Lift, Qwen3.5-9B), none yet for Qwen3-VL-32B (incomplete run); one older narrative report exists for 1 of 11 legacy-corpus documents only | `benchmarks/benchmark_5rfp_v2/reports/*.md`, `benchmarks/reports_legacy/` |
| AI Hub / playground / demo evidence | **NOT DONE** — no reference to "AI Hub" (or variants) found anywhere in the project; all live Kubernetes Services for this app are `ClusterIP`-only, no externally reachable URL exists to demo from | `APPLICATION_STATUS.md` |
| Load testing | **NOT VERIFIED** — a `loadgen` pod/job exists in the shared cluster (`ahmed` and other namespaces, `kubectl get pods -A`) but no artifact in this project ties a specific load-test run/result to this RFP application's endpoints; not claimed as done | `capstone_environment.txt` (pod list) |
| 16 GB deployment VRAM constraint | **NOT VERIFIED as literally 16GB** — the actual GPU is a 48GB RTX A6000; the project's own `serve.sh` comments document a real, measured VRAM-fitting constraint (qwen3-vl-32b-AWQ ≈20GB, llama-70b-AWQ ≈38-40GB, cannot coexist), but that is a 48GB-card constraint, not a 16GB one. If "16GB" refers to a different, specific deployment target not evidenced here, that target was not found in this project | `DEPLOYMENT_EVIDENCE.md`, `capstone_environment.txt` (nvidia-smi) |

## Additional implemented-but-not-explicitly-requested evidence found

| Item | Status | Evidence |
|---|---|---|
| FastAPI backend application (extract/chat/agent-review) | DONE | `APPLICATION_STATUS.md` |
| React/Vite frontend (EN/AR, RTL, dark mode) | DONE | `APPLICATION_STATUS.md`, `frontend_evidence/` |
| Prometheus + Grafana monitoring, live in-cluster | DONE (dashboards not independently verified) | `APPLICATION_STATUS.md` |
| Evidence/anti-hallucination mechanism (quote verification) | DONE | `BENCHMARK_METHOD.md` §5 |

## Explicit non-findings (reported, not assumed)

- No "BeamData"-labeled dataset name found anywhere in the project (if the
  underlying brief specifically named that set — the actual corpus used for the
  final benchmark is the 5 real-world RFPs in `rfps/`).
- Project directory is **not a git repository** — no commit history, branch, or
  diff evidence exists to cite (`PROJECT_HISTORY_GIT.txt`).
- No automated test suite exists anywhere in the project.

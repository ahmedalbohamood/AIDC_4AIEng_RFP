# Deployment Evidence

Generated 2026-09-27 by live, read-only inspection (`kubectl get ... -o yaml`,
`docker images`, `docker ps -a`, `nvidia-smi`, `crictl ps`, `k3s ctr images ls`).
No deployments, pods, or containers were created, deleted, scaled, or restarted to
produce this file. Raw exports are in `deployment/k8s_ahmed_live/` and
`capstone_environment.txt`.

---

## CURRENT STATE (as of 2026-09-27 ~07:17 UTC)

### Kubernetes — namespace `ahmed` (this project's live deployment)

The `ahmed` namespace is confirmed as this project's own deployment: `server.py`'s
own source comment states *"the ahmed-namespace deployment overrides [VLLM_URL] to
the in-cluster Service DNS name"* — this is not a shared/unrelated teammate
namespace, it is where this project is actually deployed.

| Deployment | Image | Replicas | Status | GPU |
|---|---|---|---|---|
| `k2-vllm` | `vllm/vllm-openai:latest` | 1/1 available | Running | 1x `nvidia.com/gpu` (request=limit) |
| `rfp-backend` | `rfp-backend:latest` (local, `imagePullPolicy: Never`) | 1/1 available | Running | none |
| `rfp-frontend` | `rfp-frontend:latest` (local) | 1/1 available | Running | none |
| `rfp-combined` | `rfp-combined:latest` (local) | 1/1 available | Running | none |
| `grafana` | `grafana/grafana:11.4.0` | 1/1 available | Running | none |
| `prometheus` | `prom/prometheus:v2.55.1` | 1/1 available | Running | none |

**`k2-vllm` full spec** (`deployment/k8s_ahmed_live/deploy-k2-vllm.yaml`):
- Args: `--model=IFM/K2-Horizon-7B --served-model-name=IFM/K2-Horizon-7B
  --max-model-len=32768 --gpu-memory-utilization=0.90 --trust-remote-code
  --chat-template=/etc/k2-template/chat_template.jinja`
- Resources: requests = limits = `nvidia.com/gpu: 1` (no explicit cpu/memory
  request/limit set on this container)
- Readiness probe: `GET /health:8000`, period 5s; startup probe same path,
  `failureThreshold: 60` (allows up to 10 min for cold model load)
- Volumes: hostPath `/home/ubuntu/.cache/huggingface` → `/root/.cache/huggingface`;
  a `chat-template` ConfigMap volume mount for the custom K2 chat template
- **Model ID:** `IFM/K2-Horizon-7B` — **quantization: none identified** (no
  `--quantization` flag in the args; vLLM defaults apply, likely full/half
  precision, not AWQ/GPTQ — treat quantization format as NOT VERIFIED for this
  specific deployment)

**`rfp-backend` / `rfp-combined` full spec:**
- Both point `VLLM_URL=http://k2-vllm:8000/v1` (in-cluster Service DNS)
- `OPENAI_API_KEY` sourced from Secret `openai-key` key `api-key` (value never
  read or printed by this collection)
- Resources: requests `cpu: 500m, memory: 512Mi`; limits `cpu: 1, memory: 1Gi`
- No GPU allocated to either (they call the GPU only via the `k2-vllm` service)
- `rfp-backend` restarted 2026-09-27T01:20:30Z (per pod annotation
  `kubectl.kubernetes.io/restartedAt`); `rfp-combined` is a separate, more
  recently-created deployment (age ~4.5h vs. ~25h for the others at inspection
  time) — the two backend deployments coexist; which one the frontend actually
  points at was not independently verified from this evidence alone (check
  `frontend_evidence/.env`'s `VITE_API_BASE_URL` / the `rfp-frontend` build if this
  matters for the report).

**Services** (all `ClusterIP`, no external `NodePort`/`LoadBalancer` on any
`ahmed` service): `k2-vllm:8000`, `rfp-backend:8420`, `rfp-combined:8420`,
`rfp-frontend:80`, `grafana:3000`, `prometheus:9090`. None of these are currently
exposed outside the cluster (no NodePort, no Ingress found for this namespace).

**GPU process, live-verified:** `nvidia-smi` shows one active CUDA process
(`VLLM::EngineCore`, 42,398 MiB / 49,140 MiB total VRAM). Cross-checked via
`crictl ps`: that process belongs to container `vllm` inside pod
`k2-vllm-5cb4cdcf68-pwjd2` (namespace `ahmed`) — **the GPU is currently running
the Kubernetes-deployed model, not a standalone Docker container.**

### Docker — model serving

**`docker ps -a` currently shows NO running or exited model-serving container**
(`vllm-bench`, `lift-vllm`) — only `dcgm-exporter` and `node-exporter` (cluster GPU
metrics sidecars, unrelated to this project). This project's k3s cluster uses
`containerd`, not the Docker daemon, to run Kubernetes pods, so `docker ps` never
shows k8s-managed containers by design — this is not itself an anomaly, but it
does mean **no plain-`docker run` model container is live right now.**

`docker images` (and `k3s ctr images ls`, since local app images are imported into
containerd for the `imagePullPolicy: Never` k8s deployments above) show these
locally-built images, all present and available for redeploy:
`rfp-backend:latest`, `rfp-frontend:latest`, `rfp-combined:latest`,
`rfp-app:demo` (built but not referenced by any current k8s Deployment — its
purpose was not independently verified from this evidence), and the pulled base
image `vllm/vllm-openai:latest` (8.1 GiB).

---

## HISTORICAL / CONFIGURED STATE (documented, not currently running)

### `serve.sh` — Docker-based local model serving (`deployment/serve.sh`)

This script is this project's actual "deploy an open-weight model via plain
Docker" path, used to run the benchmarks under `benchmark_5rfp_v2/` and
`results*/`. It supports three named model presets, one container at a time on
the shared A6000 (documented in the script's own comments as a hard VRAM
constraint — see below):

| Preset | Model | Container | Port | Launch flags |
|---|---|---|---|---|
| `qwen` | `QuantTrio/Qwen3-VL-32B-Instruct-AWQ` | `vllm-bench` | 8100 | `--quantization awq_marlin --dtype half --max-model-len 49152 --gpu-memory-utilization 0.90 --limit-mm-per-prompt '{"image":24}'` |
| `llama` | `casperhansen/llama-3.3-70b-instruct-awq` | `vllm-bench` | 8100 | `--quantization awq_marlin --dtype half --max-model-len 14336 --gpu-memory-utilization 0.95` |
| `lift` | `datalab-to/lift` | `lift-vllm` | 8200 | `--max-model-len 32768 --gpu-memory-utilization 0.85 --trust-remote-code` (no quantization — BF16) |

An earlier live inspection of this same project (`RFP_CAPSTONE_EVIDENCE.md`,
dated 2026-09-22, superseded by this file) directly confirmed, via `docker
inspect`, that `vllm-bench` was running `QuantTrio/Qwen3-VL-32B-Instruct-AWQ` live
on port 8100 at that time, with `/health` returning 200. **That container is not
running now** — the benchmark logs (`benchmark_5rfp_v2/run_manifest*.json`)
record it being explicitly stopped partway through the V2 benchmark session to
free VRAM for `lift-vllm`, and again to free VRAM for a `qwen3.5-9b-text` run; the
live GPU slot today is held by the Kubernetes `k2-vllm` pod instead.

**16GB VRAM constraint:** the actual card is a 48GB RTX A6000 (`nvidia-smi`,
`capstone_environment.txt`), not literally 16GB. `serve.sh`'s own comments record
the *effective* per-model constraint discovered by measurement: qwen3-vl-32b-AWQ
≈20GB, llama-3.3-70b-AWQ ≈38-40GB, and two of the three local models cannot
coexist with each other on this card — each serve.sh preset is written as
"stop the other one first." If the capstone's "16GB deployment VRAM constraint"
requirement means a specific 16GB-class card, this project's actual hardware
(48GB A6000) does not match that constraint as literally stated — report as
**NOT VERIFIED against a 16GB card**, not silently reconciled.

### Kubernetes — namespace `team` (a different, older, unrelated deployment)

A `vllm` Deployment exists in the `team` namespace, scaled to `0/0` replicas
(confirmed again in this pass — unchanged from the prior 2026-09-22 inspection).
Per its stored spec: image `vllm/vllm-openai:v0.27.1`, model
`Qwen/Qwen2.5-1.5B-Instruct-AWQ`. This is **not** this project's deployment (no
project file references `team-serving` or `vllm-engine`); it is dormant,
shared-pod infrastructure from a different exercise. `team/grafana`,
`team/prometheus`, `team/alert-inbox`, `team/health-shim` are likewise shared
cluster infrastructure, not built by this project.

---

## Application containers — build source

`Dockerfile.backend` (repo root `Dockerfile`, copied to `deployment/`) builds a
single Python 3.10-slim image containing `rfpbench/`, `server.py`, and the
frontend's static build output (`AI RFP System Interface (1)/dist/` copied in as
`frontend_dist/`) — i.e. backend and frontend are bundled into one image at
`EXPOSE 8420`, run via `uvicorn server:app`. This appears to be the source of the
`rfp-combined` image/deployment (name matches: "combined" = backend+frontend in
one container). `rfp-backend`/`rfp-frontend` as separate deployments imply a
second, split-image build exists too (its Dockerfile was not found as a
standalone file distinct from the frontend's own `Dockerfile.frontend`, which is
a 2-line file — not independently reconciled here; report the split-vs-combined
image provenance as **NOT FULLY VERIFIED**, since only one backend Dockerfile and
one frontend Dockerfile were found in the two project directories, yet three
distinct backend-shaped images exist: `rfp-backend`, `rfp-frontend`,
`rfp-combined`).

---

## Summary against the capstone deployment requirements

| Requirement | Status | Evidence |
|---|---|---|
| Open-weight model deployed via Docker | **HISTORICAL/CONFIGURED** — not currently running as a plain Docker container; `serve.sh` + prior live inspection confirm it was done (Qwen3-VL-32B-AWQ, live-tested 2026-09-22) | `deployment/serve.sh`; superseded evidence in `RFP_CAPSTONE_EVIDENCE.md` §4/§5 |
| Open-weight model deployed to Kubernetes | **CURRENT / DONE** — `k2-vllm` deployment, 1/1 available, GPU-verified live via `nvidia-smi`+`crictl` cross-check | `deployment/k8s_ahmed_live/deploy-k2-vllm.yaml`, `capstone_environment.txt` |
| FastAPI backend deployed to Kubernetes | **CURRENT / DONE** | `deployment/k8s_ahmed_live/deploy-rfp-backend.yaml`, `deploy-rfp-combined.yaml` |
| Frontend deployed to Kubernetes | **CURRENT / DONE** | `deployment/k8s_ahmed_live/deploy-rfp-frontend.yaml` |
| Monitoring (Prometheus/Grafana) deployed | **CURRENT / DONE** | `deployment/k8s_ahmed_live/deploy-prometheus.yaml`, `deploy-grafana.yaml` |
| External/AI-Hub-reachable endpoint | **NOT VERIFIED** — all `ahmed` services are `ClusterIP` only, no NodePort/Ingress found | `capstone_environment.txt` (kubectl get svc -A) |

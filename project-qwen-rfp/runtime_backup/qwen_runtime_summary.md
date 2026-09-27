# Qwen (`vllm-bench`) Runtime Backup

Captured: 2026-09-22, immediately before temporarily stopping the container to free
VRAM for the `datalab-to/lift` benchmark. Full raw `docker inspect` output is saved
alongside this file at `qwen_vllm_container_inspect.json`. No secret values are
recorded anywhere in this backup — only environment variable **names**.

## Identity

- **Container name:** `vllm-bench`
- **Image:** `vllm/vllm-openai:latest`
- **Served model:** `QuantTrio/Qwen3-VL-32B-Instruct-AWQ`
- **Status at capture time:** `running` (up ~13 hours)

## Command

Entrypoint: `vllm serve`

Args:
```
--model QuantTrio/Qwen3-VL-32B-Instruct-AWQ
--served-model-name QuantTrio/Qwen3-VL-32B-Instruct-AWQ
--max-model-len 32768
--gpu-memory-utilization 0.90
```

## Networking

- Port mapping: host `8100/tcp` → container `8000/tcp`

## Volumes

- Bind mount: `/home/ubuntu/hf-cache` → `/root/.cache/huggingface` (RW)

## GPU configuration

- Device request: `Driver: ""`, `Count: -1` (all GPUs), `Capabilities: [["gpu"]]`

## Restart policy

- `Name: "no"`, `MaximumRetryCount: 0` (container does NOT auto-restart on its own —
  it must be started manually with `docker start vllm-bench` after a stop)

## Environment variable NAMES only (no values recorded)

```
PATH, NVARCH, NVIDIA_REQUIRE_CUDA, NV_CUDA_CUDART_VERSION, CUDA_VERSION,
LD_LIBRARY_PATH, NVIDIA_VISIBLE_DEVICES, NVIDIA_DRIVER_CAPABILITIES,
DEBIAN_FRONTEND, UV_HTTP_TIMEOUT, UV_INDEX_STRATEGY, UV_LINK_MODE,
UV_PYTHON_INSTALL_DIR, UV_CACHE_DIR, UV_OVERRIDE, VLLM_ENABLE_CUDA_COMPATIBILITY,
TORCH_CUDA_ARCH_LIST, VLLM_USAGE_SOURCE, VLLM_BUILD_COMMIT, VLLM_BUILD_PIPELINE,
VLLM_BUILD_URL, VLLM_IMAGE_TAG
```

(These are all image-baked build/CUDA vars — none is an API-key or secret-named
variable. This matches the finding in `RFP_CAPSTONE_EVIDENCE.md` §5.)

## How to restore exactly this setup

The container was stopped with `docker stop vllm-bench`, **not removed**. To bring
Qwen back exactly as it was:

```bash
docker start vllm-bench
```

This reuses the existing container (same image, command, port mapping, volume
mount, GPU request) with no reconfiguration needed. Only use `docker run ...`
to recreate it from scratch if the container object itself is ever deleted
(it was not deleted as part of this task).

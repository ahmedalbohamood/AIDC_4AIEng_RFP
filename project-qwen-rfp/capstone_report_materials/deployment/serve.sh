#!/usr/bin/env bash
# Serve one local model on the A6000 via vLLM's OpenAI-compatible API.
#
#   ./serve.sh qwen     # Qwen3-VL-32B-Instruct-AWQ  (vision)   -> vllm-bench :8100
#   ./serve.sh llama    # Llama-3.3-70B-Instruct-AWQ (text)     -> vllm-bench :8100
#   ./serve.sh lift      # datalab-to/lift (vision, extraction)  -> lift-vllm  :8200
#   ./serve.sh stop
#   ./serve.sh lift-stop
#
# qwen/llama share one container (vllm-bench) and ONE AT A TIME: 20GB + 40GB of
# weights do not coexist on a 48GB card; starting the second while the first is
# up gets you a CUDA OOM during weight loading.
#
# lift runs as its own container (lift-vllm) on its own port (8200) so it does
# not overwrite whichever of qwen/llama is currently configured on vllm-bench -
# added 2026-09-22 for the additive Lift benchmark integration. Still check
# `nvidia-smi` before starting it alongside another running model: a 9B BF16
# model is ~18-20GB, and two live models must both fit in 48GB total.
set -euo pipefail

CACHE=/home/ubuntu/hf-cache
NAME=vllm-bench
PORT=8100
LIFT_NAME=lift-vllm
LIFT_PORT=8200

stop() {
  docker rm -f "$NAME" >/dev/null 2>&1 || true
  echo "stopped $NAME"
}

lift_stop() {
  docker rm -f "$LIFT_NAME" >/dev/null 2>&1 || true
  echo "stopped $LIFT_NAME"
}

case "${1:-}" in
  stop) stop; exit 0 ;;
  lift-stop) lift_stop; exit 0 ;;
  lift)
    lift_stop
    echo "starting datalab-to/lift ..."
    docker run -d --name "$LIFT_NAME" --gpus all \
      -v "$CACHE:/root/.cache/huggingface" \
      -p "$LIFT_PORT:8000" \
      --ipc=host \
      vllm/vllm-openai:latest \
      --model datalab-to/lift \
      --served-model-name datalab-to/lift \
      --max-model-len 32768 \
      --gpu-memory-utilization 0.85 \
      --trust-remote-code
    echo "waiting for /health"
    for i in $(seq 1 120); do
      if curl -sf "http://localhost:$LIFT_PORT/health" >/dev/null 2>&1; then
        echo "ready after ${i}0s"
        curl -s "http://localhost:$LIFT_PORT/v1/models" | head -c 400; echo
        exit 0
      fi
      if ! docker ps --format '{{.Names}}' | grep -q "^$LIFT_NAME$"; then
        echo "container died; last 40 lines:" >&2
        docker logs "$LIFT_NAME" 2>&1 | tail -40 >&2
        exit 1
      fi
      sleep 10
    done
    echo "timed out; check: docker logs $LIFT_NAME" >&2
    exit 1
    ;;
  qwen)
    MODEL=QuantTrio/Qwen3-VL-32B-Instruct-AWQ
    # limit-mm-per-prompt is the one that bites: vLLM defaults to 1 image per
    # request and the harness sends up to 16 rendered pages in a single call.
    # Without this the server 400s on every vision cluster.
    EXTRA=(--max-model-len 49152
           --gpu-memory-utilization 0.90
           --limit-mm-per-prompt '{"image":24}')
    ;;
  llama)
    MODEL=casperhansen/llama-3.3-70b-instruct-awq
    # ~40GB of weights leaves very little for KV cache. Measured directly: at
    # max-model-len 16384 vLLM's own profiler reported needing 5.0 GiB of KV
    # cache against 4.84 GiB available, and named 15856 as the actual ceiling.
    # 14336 leaves real margin below that (not just under by 528 tokens) and
    # still comfortably covers our largest text cluster (~11k tokens for a
    # 39-page RFP).
    EXTRA=(--max-model-len 14336
           --gpu-memory-utilization 0.95)
    ;;
  *) echo "usage: $0 {qwen|llama|lift|stop|lift-stop}" >&2; exit 1 ;;
esac

stop
echo "starting $MODEL ..."
docker run -d --name "$NAME" --gpus all \
  -v "$CACHE:/root/.cache/huggingface" \
  -p "$PORT:8000" \
  --ipc=host \
  vllm/vllm-openai:latest \
  --model "$MODEL" \
  --served-model-name "$MODEL" \
  --quantization awq_marlin \
  --dtype half \
  "${EXTRA[@]}"

echo "waiting for /health (engines load slowly; ctrl-C is safe, the container keeps loading)"
for i in $(seq 1 120); do
  if curl -sf "http://localhost:$PORT/health" >/dev/null 2>&1; then
    echo "ready after ${i}0s"
    curl -s "http://localhost:$PORT/v1/models" | head -c 400; echo
    exit 0
  fi
  if ! docker ps --format '{{.Names}}' | grep -q "^$NAME$"; then
    echo "container died; last 40 lines:" >&2
    docker logs "$NAME" 2>&1 | tail -40 >&2
    exit 1
  fi
  sleep 10
done
echo "timed out; check: docker logs $NAME" >&2
exit 1

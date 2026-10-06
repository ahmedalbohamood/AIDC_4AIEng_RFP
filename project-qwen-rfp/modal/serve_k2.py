"""Serves IFM/K2-Horizon-7B on Modal via vLLM's OpenAI-compatible API - a
drop-in replacement for the academy A6000 (serve.sh) / k8s (deploy-k2-vllm.yaml)
deployment, now that that GPU is gone.

Same image family (vllm/vllm-openai), same model, same flags, same custom chat
template as the k8s deployment (k2-chat-template configmap) - this exists
because K2-Horizon-7B has no native vLLM plugin and runs through the generic
Transformers chat-template fallback, which 400s on system-role messages unless
given this template (see rfpbench/backends.py's merge_system_into_user comment
for the client-side half of this same workaround).

Deploy:
    pip install modal
    modal setup                        # one-time browser login
    modal deploy modal/serve_k2.py

Deploying prints an HTTPS URL like:
    https://<workspace>--k2-horizon-rfp-serve.modal.run

Point the backend at it:
    VLLM_URL=https://<workspace>--k2-horizon-rfp-serve.modal.run/v1

First request after a cold start pulls ~15GB of weights and can take a few
minutes; container stays warm for scaledown_window after the last request.
"""
from pathlib import Path

import modal

MODEL_NAME = "IFM/K2-Horizon-7B"
VLLM_PORT = 8000
MINUTES = 60

app = modal.App("k2-horizon-rfp")

vllm_image = (
    modal.Image.from_registry("vllm/vllm-openai:latest", add_python="3.12")
    .entrypoint([])  # drop the base image's baked-in ENTRYPOINT so Modal can invoke our function
    .add_local_file(
        local_path=str(Path(__file__).parent / "chat_template.jinja"),
        remote_path="/root/chat_template.jinja",
    )
)

hf_cache_vol = modal.Volume.from_name("hf-cache", create_if_missing=True)

# If IFM/K2-Horizon-7B ever requires auth, create this with:
#   modal secret create huggingface-secret HF_TOKEN=hf_...
# and add `secrets=[modal.Secret.from_name("huggingface-secret")]` below.


@app.function(
    image=vllm_image,
    gpu="L40S",  # 48GB, same class as the original A6000; drop to "A10G" to save cost if it fits
    volumes={"/root/.cache/huggingface": hf_cache_vol},
    scaledown_window=15 * MINUTES,
    timeout=20 * MINUTES,
)
@modal.concurrent(max_inputs=32)
@modal.web_server(port=VLLM_PORT, startup_timeout=15 * MINUTES)
def serve():
    import subprocess

    cmd = (
        f"vllm serve {MODEL_NAME} "
        f"--served-model-name {MODEL_NAME} "
        f"--max-model-len 32768 "
        f"--gpu-memory-utilization 0.90 "
        f"--trust-remote-code "
        f"--chat-template /root/chat_template.jinja "
        f"--host 0.0.0.0 --port {VLLM_PORT}"
    )
    subprocess.Popen(cmd, shell=True)

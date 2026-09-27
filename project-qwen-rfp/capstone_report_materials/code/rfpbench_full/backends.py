"""The three models behind one interface.

All three speak the OpenAI chat-completions API - GPT-4o at api.openai.com, and the
two local models through vLLM's OpenAI-compatible server - so the harness has
exactly one call path and differences in results cannot be blamed on differences in
client code.

Two things differ per backend and are declared, not hidden:

  modality        text | vision. A vision backend receives rendered page images; a
                  text backend receives extracted page text. This is a real
                  confound - you are comparing pipelines, not just weights - which
                  is why GPT-4o is registered twice, once each way, as the control
                  that lets you separate "modality" from "model".

  schema_mode     how structured output is enforced: OpenAI strict json_schema, or
                  vLLM guided_json. Both guarantee parseable JSON; neither
                  guarantees correct content.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Optional

from openai import OpenAI


def _salvage_partial_json(text: str) -> Optional[dict]:
    """When a completion breaks mid-object - truncated, or stuck in the
    infinite-whitespace-loop pathology documented on Backend.call() - recover
    whichever top-level fields DID finish generating rather than losing the
    entire cluster to the one field that was mid-generation when it broke. A
    crash there is strictly worse than just missing that one field: every other
    field in the same call already completed correctly and is worth keeping.
    """
    text = text.strip()
    if not text.startswith("{"):
        return None
    depth = 0
    in_string = False
    escape = False
    last_good_end = None
    for i, ch in enumerate(text):
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch in "{[":
            depth += 1
        elif ch in "}]":
            depth -= 1
            if depth == 1 and ch == "}":
                last_good_end = i + 1     # just closed one top-level field's value
    if last_good_end is None:
        return None
    try:
        return json.loads(text[:last_good_end] + "}")
    except json.JSONDecodeError:
        return None


# USD per 1M tokens. Local models cost no API dollars; their cost is GPU time,
# tracked separately as latency (see runner).
PRICING = {
    "gpt-4o": {"in": 2.50, "out": 10.00},
}


def _merge_system_into_user(messages: list) -> list:
    """Fold a leading system message into the first user message. See
    Backend.merge_system_into_user for why this workaround exists."""
    if not messages or messages[0].get("role") != "system":
        return messages
    system_content = messages[0]["content"]
    rest = messages[1:]
    if rest and rest[0].get("role") == "user":
        merged = dict(rest[0])
        merged["content"] = f"{system_content}\n\n{rest[0]['content']}"
        return [merged] + rest[1:]
    return [{"role": "user", "content": system_content}] + rest


@dataclass
class CallResult:
    parsed: Optional[dict]
    raw_text: str
    ok: bool
    error: Optional[str]
    latency_s: float
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float


@dataclass
class Backend:
    name: str                 # how it appears in results/ and the writeup
    model: str                # the model id the endpoint expects
    modality: str             # "text" | "vision"
    base_url: Optional[str] = None
    api_key_env: str = "OPENAI_API_KEY"
    schema_mode: str = "openai_strict"   # "openai_strict" | "vllm_guided"
    # 4096 was pure unused headroom - the largest real response measured across
    # every model and cluster was 1463 completion tokens - and it caused a real
    # failure: reserving 4096 output tokens against Llama-70B's 14336-token context
    # pushed one large `commercial` cluster (19 pages, 10241 input tokens) one
    # token over the limit and 400'd. 2048 keeps ~40% margin over the largest
    # observed response without eating into context headroom that input needs.
    max_tokens: int = 2048
    temperature: float = 0.0
    # Newer OpenAI reasoning-tier models (gpt-5.x) reject the classic chat params:
    # 'max_tokens' -> 'max_completion_tokens', and temperature is fixed at the
    # model's default (they 400 on any explicit value, including 0.0). Set both
    # flags together for those backends.
    fixed_temperature: bool = False
    # Live-incident workaround (2026-09-27): the current vllm/vllm-openai:latest
    # pull serving K2-Horizon-7B (K2HorizonForCausalLM, no native vLLM plugin -
    # runs via the generic Transformers chat-template fallback) throws a 400 on
    # ANY request containing a system-role message: "can only concatenate str
    # (not 'list') to str", raised by vLLM's own hf.py chat-template application
    # - confirmed with raw curl, no client library involved, and confirmed the
    # exact same messages succeed once merged into a single user-role message.
    # Every extraction and agent call uses a system message, so until this is
    # fixed upstream (or the image is pinned to a version from before the
    # regression), every k2-horizon-7b call needs this merge to get a real
    # answer instead of a silent empty one.
    merge_system_into_user: bool = False
    _client: OpenAI = field(default=None, repr=False)

    def client(self) -> OpenAI:
        if self._client is None:
            key = os.environ.get(self.api_key_env)
            if not key:
                if self.base_url:          # local vLLM: any non-empty string works
                    key = "not-needed"
                else:
                    raise RuntimeError(
                        f"{self.name}: environment variable {self.api_key_env} is not set. "
                        f"Put it in project-qwen-rfp/.env")
            self._client = OpenAI(api_key=key, base_url=self.base_url, timeout=300.0)
        return self._client

    def call(self, messages: list, schema: dict, schema_name: str) -> CallResult:
        result = self._call_once(messages, schema, schema_name, self.temperature)
        if result.ok:
            return result

        # Retry once with a small temperature bump rather than a permanent sampling
        # change. Root cause (2026-09-21): under guided decoding, some vLLM models
        # occasionally fall into an infinite whitespace-repetition loop emitting an
        # empty list/table value and never close it, burning the whole completion
        # budget. Tried as permanent fixes and rejected: presence_penalty (fixed
        # one doc, failed identically even at 1.5-2.0 on a second doc - unreliable)
        # and frequency_penalty (fixed the crash but silently corrupted OTHER,
        # unrelated fields in the same call - confidence=-2.0, garbage numbers,
        # present=true with value="" - worse than a detectable crash). A pure
        # greedy decode (temperature=0) has exactly one path forward at each step,
        # so once it's in the loop it cannot escape; a small amount of randomness
        # only on the retry lets it sample a different, still-plausible token
        # instead, without changing the deterministic common case at all.
        if not (result.error and "unparseable JSON" in result.error):
            return result
        retry = self._call_once(messages, schema, schema_name, temperature=0.3)
        retry.prompt_tokens += result.prompt_tokens
        retry.completion_tokens += result.completion_tokens
        retry.cost_usd += result.cost_usd
        retry.latency_s += result.latency_s
        if retry.ok:
            return retry

        # Both attempts broke - measured directly, the temperature bump reduces
        # but does not reliably prevent the loop (still failed on a second
        # document even after succeeding on the first). Rather than lose every
        # field in the cluster to whichever one field was mid-generation when it
        # broke, salvage whichever top-level fields DID finish from the longer of
        # the two raw completions and return those as a genuine (partial) result -
        # every field the runner doesn't see here still correctly grades as
        # "missing" instead of the whole cluster doing so.
        longer_text = max(result.raw_text, retry.raw_text, key=len)
        salvaged = _salvage_partial_json(longer_text)
        if salvaged:
            return CallResult(salvaged, longer_text, True,
                              f"partial (salvaged {len(salvaged)} of {len(schema.get('properties', {}))} fields "
                              f"after: {retry.error})",
                              retry.latency_s, retry.prompt_tokens, retry.completion_tokens, retry.cost_usd)
        return retry

    def _call_once(self, messages: list, schema: dict, schema_name: str,
                   temperature: float) -> CallResult:
        if self.merge_system_into_user:
            messages = _merge_system_into_user(messages)
        kwargs = {"model": self.model, "messages": messages}
        if self.fixed_temperature:
            kwargs["max_completion_tokens"] = self.max_tokens
        else:
            kwargs["temperature"] = temperature
            kwargs["max_tokens"] = self.max_tokens
        if self.schema_mode in ("openai_strict", "vllm_guided"):
            # Deliberately the SAME mechanism for both families.
            #
            # vLLM's older `guided_json` + guided_decoding_backend path does not
            # enforce the schema's `required` list: measured on Qwen3-VL, all three
            # backends (xgrammar, outlines, guidance) happily returned
            # {present, value, page} and silently dropped `quote` and `confidence`,
            # which are exactly the fields this benchmark grades on. The model then
            # scores 0% grounded for a reason that has nothing to do with the model.
            # Via response_format the same request returns all six keys with a full
            # verbatim quote. Holding both families to one mechanism is also the
            # only way the comparison means anything.
            kwargs["response_format"] = {
                "type": "json_schema",
                "json_schema": {"name": schema_name, "schema": schema, "strict": True},
            }
        else:
            raise ValueError(f"unknown schema_mode {self.schema_mode}")

        started = time.monotonic()
        try:
            response = self.client().chat.completions.create(**kwargs)
        except Exception as exc:                      # network, 4xx, context overflow
            return CallResult(None, "", False, f"{type(exc).__name__}: {exc}",
                              time.monotonic() - started, 0, 0, 0.0)
        latency = time.monotonic() - started

        text = response.choices[0].message.content or ""
        usage = response.usage
        p_tok = getattr(usage, "prompt_tokens", 0) or 0
        c_tok = getattr(usage, "completion_tokens", 0) or 0

        price = PRICING.get(self.name, {"in": 0.0, "out": 0.0})
        cost = (p_tok * price["in"] + c_tok * price["out"]) / 1_000_000

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            # With structured output on, this should be unreachable. When it does
            # happen it is nearly always a truncated response (max_tokens too low),
            # so it is worth distinguishing in the results rather than silently
            # counting it as a wrong answer.
            return CallResult(None, text, False, f"unparseable JSON: {exc}",
                              latency, p_tok, c_tok, cost)

        return CallResult(parsed, text, True, None, latency, p_tok, c_tok, cost)


def default_backends(vllm_url: str = "http://localhost:8100/v1",
                     lift_url: str = "http://localhost:8200/v1") -> dict:
    """The benchmark roster.

    gpt-4o-text and gpt-4o-vision are the same model on the same documents through
    different input pipelines. Running both is cheap and is the only way to say how
    much of any gap to the local models is the model rather than the PDF pipeline.

    lift-vision runs on its own port/server (default 8200) rather than sharing
    vllm_url, since it is typically served as a separate container alongside (or
    instead of) whichever other local model is currently up - see LIFT_BASE_URL.
    """
    return {
        "gpt-4o-text": Backend(
            name="gpt-4o", model="gpt-4o", modality="text",
            schema_mode="openai_strict",
        ),
        "gpt-4o-vision": Backend(
            name="gpt-4o", model="gpt-4o", modality="vision",
            schema_mode="openai_strict",
        ),
        "gpt-5.5-vision": Backend(
            # Added 2026-09-21: user asked to try a frontier reasoning model with
            # no time budget, specifically for native document/PDF understanding
            # rather than our own text-extraction layer (PyMuPDF/Docling), which
            # has been the source of several bugs this session (jumbled tables,
            # multi-page continuation). Reads page images directly, same as
            # gpt-4o-vision, just a far more capable model behind it.
            name="gpt-5.5", model="gpt-5.5", modality="vision",
            schema_mode="openai_strict", max_tokens=8000, fixed_temperature=True,
        ),
        "qwen3-vl-32b": Backend(
            name="qwen3-vl-32b", model="QuantTrio/Qwen3-VL-32B-Instruct-AWQ",
            modality="vision", base_url=vllm_url, schema_mode="vllm_guided",
            # 2048 (the shared default) truncated the `commercial` cluster (7
            # fields, 14 pages after the vision page cap) on City of Medicine Hat -
            # completion_tokens hit the cap on both the primary attempt and the
            # retry (3932 accumulated), losing the last 3 of 7 fields even with
            # salvage recovering the first 4. Same fix as qwen3.5-9b: give the
            # larger clusters real room instead of relying on salvage as the
            # normal path (2026-09-22).
            max_tokens=3072,
        ),
        "llama-70b": Backend(
            name="llama-70b", model="casperhansen/llama-3.3-70b-instruct-awq",
            modality="text", base_url=vllm_url, schema_mode="vllm_guided",
        ),
        "qwen3.5-9b": Backend(
            # Officially text+vision (Qwen3_5ForConditionalGeneration), but run as
            # text here to compare against the same-modality field (Llama-70B,
            # GPT-4o-text) the user actually cares about: extraction speed.
            name="qwen3.5-9b", model="QuantTrio/Qwen3.5-9B-AWQ",
            modality="text", base_url=vllm_url, schema_mode="vllm_guided",
            # 2048 (the shared default) truncated the `commercial` cluster (7
            # fields) mid-JSON on 04_Data_Centre_Download_Integration_Services_RFP.
            # Root cause found by reproducing the raw completion directly: right
            # after `"present": false, "value":` for insurance_requirements (an
            # empty List[InsuranceRow]), the model fell into an infinite
            # whitespace-repetition loop under guided decoding and never closed
            # the array. Tried and rejected as fixes: schema field-reordering
            # (didn't help); presence_penalty (fixed one doc at 0.3-0.4, failed
            # identically even at 1.5-2.0 on a second doc - unreliable);
            # frequency_penalty=1.0 (fixed JSON validity but silently corrupted
            # OTHER fields in the same object - empty values marked present,
            # confidence=-2.0, garbage numbers - worse than the crash since it
            # can pass as valid JSON while being wrong). The actual fix is a
            # retry, not a permanent sampling change: Backend.call() now retries
            # once with a small temperature bump only when the first attempt's
            # JSON fails to parse, so the common case stays fully deterministic
            # (2026-09-21).
            max_tokens=3072,
        ),
        "k2-horizon-7b": Backend(
            # Runs via vLLM's generic Transformers-fallback path, not a native
            # kernel implementation (no vLLM plugin ships for K2HorizonForCausalLM)
            # - expect this to be the slowest per-token of the small models.
            name="k2-horizon-7b", model="IFM/K2-Horizon-7B",
            modality="text", base_url=vllm_url, schema_mode="vllm_guided",
            # 2048 (the shared default) let the commercial_pricing cluster's known
            # whitespace-repetition loop (see call()'s retry comment) burn the
            # whole budget on both the original AND the temperature-bumped retry
            # on EN_-_ERP_RFP_24.25.04 (2026-09-26) - lost 3 of 4 fields to salvage.
            # qwen3.5-9b/qwen3-vl-32b/lift already carry this same 3072 bump for
            # the identical failure mode; k2-horizon-7b had simply never hit it
            # in earlier runs and so never received the fix.
            max_tokens=3072,
            # See merge_system_into_user's own docstring/comment - a live
            # regression in this exact image, not something to remove reflexively.
            merge_system_into_user=True,
        ),
        "lift-vision": Backend(
            # Added 2026-09-22: datalab-to/lift, a 9B Qwen3.5-based model purpose-built
            # for schema-constrained document extraction (not a general chatbot fine-
            # tune). Served the same way as the other local backends - vLLM's
            # OpenAI-compatible server, this project's one call path - on a dedicated
            # port (8200) so it runs alongside/instead of whichever other local model
            # is currently up rather than overwriting its config. Uses this project's
            # existing 17-field schema unmodified (json_schema() in schema.py already
            # emits present/value/page/quote/confidence per field, which is exactly
            # the evidence contract Lift is asked to satisfy) - no separate schema or
            # output adapter needed since Lift speaks the same OpenAI
            # response_format=json_schema contract as every other backend here.
            name="lift", model="datalab-to/lift",
            modality="vision", base_url=lift_url, schema_mode="vllm_guided",
            max_tokens=3072,
        ),
    }

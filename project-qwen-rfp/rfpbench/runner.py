"""Orchestration: (document x model) -> one results file, with evidence checked.

Result files are the unit of everything downstream. They hold the extracted values,
the full provenance (which pages were shown, what it cost, how long it took), and
the outcome of the quote check - which gives a real quality signal before any
ground truth exists.
"""
from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from .backends import Backend
from .document import Document, find_quote, select_pages
from .fields import BY_KEY, CLUSTERS
from .prompts import build_messages
from .schema import json_schema


def run_document(doc: Document, backend: Backend, clusters: Optional[List[str]] = None,
                 k_pages: int = 8, dpi: int = 150, verbose: bool = True,
                 full_text: bool = False) -> dict:
    clusters = clusters or list(CLUSTERS)
    started = datetime.now(timezone.utc)
    wall_clock_start = time.perf_counter()

    # Full-text mode exists to take keyword retrieval out of the measurement: on a
    # 30-page RFP against a 32k context there is room to show the whole document, so
    # a miss is the model's and not the page selector's. It is text-only - the same
    # document as page images is 1-2k vision tokens per page and does not fit - so a
    # vision backend silently keeps using selection, and the record says which it got.
    full_text = full_text and backend.modality == "text"

    record = {
        "doc_id": doc.doc_id,
        "doc_path": str(doc.path),
        "n_pages": doc.n_pages,
        "text_extractable": doc.is_text_extractable(),
        "backend": backend.name,
        "backend_key": f"{backend.name}:{backend.modality}",
        "model": backend.model,
        "modality": backend.modality,
        "retrieval": "full_text" if full_text else "selected",
        "started_at": started.isoformat(timespec="seconds"),
        "clusters": {},
        "fields": {},
        "totals": {"prompt_tokens": 0, "completion_tokens": 0,
                   "cost_usd": 0.0, "latency_s": 0.0, "errors": 0},
    }

    # A scanned PDF has no text layer; feeding that to a text backend measures
    # nothing. Record it loudly rather than letting it look like a model failure.
    if backend.modality == "text" and not record["text_extractable"]:
        record["warning"] = ("PDF has little or no extractable text (likely scanned). "
                             "A text-modality model cannot see this document without OCR.")

    # Vision backends pay ~1-2k tokens PER PAGE IMAGE, unlike text where more
    # pages is comparatively cheap - confirmed by a real 400 (context overflow)
    # on 4 of 5 docs in one run once retrieval was widened to fix a different
    # bug (see select_pages' max_pages docstring). Capped only for vision.
    vision_page_cap = 14 if backend.modality == "vision" else None

    # Retrieval (select_pages) is local and cheap - the wall-clock cost is entirely
    # the network round-trip to the model, and the 6 clusters are independent of
    # each other (different fields, different pages, different schema, no shared
    # state), so there is nothing to gain from making the model calls wait on one
    # another. Firing them concurrently and letting vLLM's continuous batching (or
    # the provider's own concurrency) overlap them changes only wall-clock time -
    # the prompts sent and answers returned are identical to the sequential version.
    per_cluster = {}
    for cluster in clusters:
        pages = doc.pages if full_text else select_pages(doc, cluster, k=k_pages,
                                                          max_pages=vision_page_cap)
        messages = build_messages(cluster, pages, backend.modality, doc.doc_id, dpi=dpi)
        schema = json_schema(cluster)
        per_cluster[cluster] = {"pages": pages, "messages": messages, "schema": schema}

        if verbose:
            shown = f"all {len(pages)} pages" if full_text else str([p.number for p in pages])
            print(f"  [{backend.name}/{backend.modality}] {doc.doc_id} :: {cluster} "
                  f"-> pages {shown}", flush=True)

    # Cap concurrency rather than firing all clusters at once (2026-09-26): with
    # every cluster in flight simultaneously against a single local vLLM instance,
    # measured directly on the Rocky View doc, one cluster's generation was cut off
    # before completing its JSON under the extra concurrent load and 3 fields came
    # back with no answer at all - the same "stops mid-JSON under load" failure
    # mode already known from vision backends, now showing up on a text backend
    # under request-level GPU contention instead of image-payload size. Capping at
    # 3 concurrent requests trades away some of the parallel speedup for less
    # engine-batching pressure per request.
    max_workers = min(3, len(clusters))
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        future_to_cluster = {
            pool.submit(backend.call, info["messages"], info["schema"], schema_name=cluster): cluster
            for cluster, info in per_cluster.items()
        }
        results = {}
        for future in as_completed(future_to_cluster):
            results[future_to_cluster[future]] = future.result()

    for cluster in clusters:
        pages = per_cluster[cluster]["pages"]
        result = results[cluster]

        record["clusters"][cluster] = {
            "pages_shown": [p.number for p in pages],
            "ok": result.ok,
            "error": result.error,
            "latency_s": round(result.latency_s, 2),
            "prompt_tokens": result.prompt_tokens,
            "completion_tokens": result.completion_tokens,
            "cost_usd": round(result.cost_usd, 6),
        }
        record["totals"]["prompt_tokens"] += result.prompt_tokens
        record["totals"]["completion_tokens"] += result.completion_tokens
        record["totals"]["cost_usd"] += result.cost_usd
        record["totals"]["latency_s"] += result.latency_s

        if not result.ok:
            record["totals"]["errors"] += 1
            if verbose:
                print(f"      ERROR ({cluster}): {result.error}", flush=True)
            continue

        for key, answer in (result.parsed or {}).items():
            if key not in BY_KEY:
                continue                      # schema forbids this, but never trust it
            record["fields"][key] = _check_evidence(doc, key, answer)

    record["totals"]["latency_s"] = round(record["totals"]["latency_s"], 2)
    record["totals"]["cost_usd"] = round(record["totals"]["cost_usd"], 6)
    # Sum of per-call latencies (above) no longer equals real elapsed time now that
    # calls run concurrently - this is the number that actually reflects the speedup.
    record["totals"]["wall_clock_s"] = round(time.perf_counter() - wall_clock_start, 2)
    record["finished_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    record["summary"] = summarise(record)
    return record


def _check_evidence(doc: Document, key: str, answer: dict) -> dict:
    """Attach the quote-verification verdict to one field answer."""
    answer = dict(answer)
    answer["_field_type"] = BY_KEY[key].type.value

    if not answer.get("present"):
        answer["_evidence"] = {"status": "absent"}
        return answer

    quote = answer.get("quote")
    claimed_page = answer.get("page")
    check = find_quote(doc, quote or "", claimed_page)

    if not quote:
        status = "no_quote"                 # claimed present but offered no evidence
    elif check["found"] and check["found_on_page"] == claimed_page:
        status = "verified"
    elif check["found"]:
        status = "wrong_page"               # grounded, but cited the wrong page
    else:
        status = "unverified"               # quote occurs nowhere: fabricated

    answer["_evidence"] = {
        "status": status,
        "claimed_page": claimed_page,
        "found_on_page": check["found_on_page"],
        "exact": check["exact"],
        "best_score": round(check["best_score"], 1),
    }
    return answer


def summarise(record: dict) -> dict:
    """Pre-ground-truth quality signal: how much of what the model asserted is
    actually grounded in the document."""
    counts = {"verified": 0, "wrong_page": 0, "unverified": 0, "no_quote": 0, "absent": 0}
    for answer in record["fields"].values():
        counts[answer["_evidence"]["status"]] = counts.get(answer["_evidence"]["status"], 0) + 1

    asserted = counts["verified"] + counts["wrong_page"] + counts["unverified"] + counts["no_quote"]
    grounded = counts["verified"] + counts["wrong_page"]
    return {
        "fields_returned": len(record["fields"]),
        "fields_asserted_present": asserted,
        "fields_absent": counts["absent"],
        "evidence": counts,
        "groundedness": round(grounded / asserted, 3) if asserted else None,
        "hallucination_rate": round(
            (counts["unverified"] + counts["no_quote"]) / asserted, 3) if asserted else None,
    }


def save(record: dict, out_dir: Path) -> Path:
    key = record["backend_key"].replace(":", "-").replace("/", "-")
    target = Path(out_dir) / key
    target.mkdir(parents=True, exist_ok=True)
    path = target / f"{record['doc_id']}.json"
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False))
    return path

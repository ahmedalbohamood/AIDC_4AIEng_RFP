#!/usr/bin/env python3
"""Run the RFP field-extraction benchmark.

    ./.venv/bin/python run.py --list                      # what is registered
    ./.venv/bin/python run.py --dry-run                   # page selection, no API calls
    ./.venv/bin/python run.py -m gpt-4o-text              # one model, all docs
    ./.venv/bin/python run.py -m gpt-4o-text -m gpt-4o-vision --limit 1
    ./.venv/bin/python run.py --all                       # every registered backend

Local backends need their vLLM server up first; only one of the two local models
fits on a 48GB A6000 at a time, so run them in separate passes.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from rfpbench.backends import default_backends
from rfpbench.document import Document, select_pages
from rfpbench.fields import CLUSTERS, FIELDS
from rfpbench.runner import run_document, save

ROOT = Path(__file__).parent


def main() -> int:
    load_dotenv(ROOT / ".env")

    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--docs", default=str(ROOT / "docs"), help="directory of RFP PDFs")
    ap.add_argument("--out", default=str(ROOT / "results"), help="where results land")
    ap.add_argument("-m", "--model", action="append", dest="models",
                    help="backend key; repeatable")
    ap.add_argument("--all", action="store_true", help="run every registered backend")
    ap.add_argument("--clusters", help="comma-separated subset of field clusters")
    ap.add_argument("--limit", type=int, help="only the first N documents")
    ap.add_argument("--pages", type=int, default=8, help="candidate pages per cluster")
    ap.add_argument("--full-text", action="store_true",
                    help="show text backends the whole document instead of selected "
                         "pages (ignored for vision backends)")
    ap.add_argument("--dpi", type=int, default=150, help="render DPI for vision models")
    ap.add_argument("--docling", action="store_true",
                    help="extract page text with Docling instead of PyMuPDF - keeps "
                         "table columns as real markdown tables; cached to "
                         ".docling_cache/ after the first (slow, ~2s/page) run")
    ap.add_argument("--vllm-url", default="http://localhost:8100/v1")
    ap.add_argument("--lift-url",
                    default=os.environ.get("LIFT_BASE_URL", "http://127.0.0.1:8200/v1"),
                    help="datalab-to/lift vLLM endpoint; also settable via LIFT_BASE_URL")
    ap.add_argument("--dry-run", action="store_true",
                    help="show page selection and exit without calling any model")
    ap.add_argument("--list", action="store_true", help="list backends and fields, then exit")
    args = ap.parse_args()

    backends = default_backends(vllm_url=args.vllm_url, lift_url=args.lift_url)

    if args.list:
        print("Backends:")
        for key, backend in backends.items():
            where = backend.base_url or "api.openai.com"
            print(f"  {key:16s} model={backend.model:45s} modality={backend.modality:6s} {where}")
        print(f"\nFields ({len(FIELDS)}) by cluster:")
        for cluster in CLUSTERS:
            keys = [f.key for f in FIELDS if f.cluster == cluster]
            print(f"  {cluster:18s} {', '.join(keys)}")
        return 0

    docs_dir = Path(args.docs)
    docs_dir.mkdir(parents=True, exist_ok=True)
    pdfs = sorted(docs_dir.glob("*.pdf"))
    if args.limit:
        pdfs = pdfs[:args.limit]
    if not pdfs:
        print(f"No PDFs in {docs_dir}. Drop RFP files there and re-run.", file=sys.stderr)
        return 1

    clusters = args.clusters.split(",") if args.clusters else list(CLUSTERS)
    for cluster in clusters:
        if cluster not in CLUSTERS:
            print(f"Unknown cluster {cluster!r}; known: {', '.join(CLUSTERS)}", file=sys.stderr)
            return 1

    if args.dry_run:
        for pdf in pdfs:
            doc = Document.load(pdf)
            flag = "" if doc.is_text_extractable() else "  [NO TEXT LAYER - scanned?]"
            print(f"\n{doc.doc_id}  ({doc.n_pages} pages){flag}")
            for cluster in clusters:
                pages = select_pages(doc, cluster, k=args.pages)
                print(f"  {cluster:18s} -> pages {[p.number for p in pages]}")
        return 0

    if args.all:
        selected = list(backends)
    elif args.models:
        selected = args.models
    else:
        print("Pick backends with -m/--model or --all (see --list).", file=sys.stderr)
        return 1
    for key in selected:
        if key not in backends:
            print(f"Unknown backend {key!r}; known: {', '.join(backends)}", file=sys.stderr)
            return 1

    out_dir = Path(args.out)
    grand = {"cost_usd": 0.0, "latency_s": 0.0, "wall_clock_s": 0.0, "errors": 0}

    for key in selected:
        backend = backends[key]
        print(f"\n=== {key} ({backend.model}, {backend.modality}) ===")
        for pdf in pdfs:
            doc = Document.load(pdf, use_docling=args.docling)
            record = run_document(doc, backend, clusters=clusters,
                                  k_pages=args.pages, dpi=args.dpi,
                                  full_text=args.full_text)
            path = save(record, out_dir)
            s = record["summary"]
            print(f"  -> {os.path.relpath(path, ROOT)}  "
                  f"present={s['fields_asserted_present']} absent={s['fields_absent']} "
                  f"grounded={s['groundedness']} halluc={s['hallucination_rate']} "
                  f"${record['totals']['cost_usd']:.4f} "
                  f"{record['totals']['wall_clock_s']:.1f}s wall "
                  f"({record['totals']['latency_s']:.1f}s summed)")
            grand["cost_usd"] += record["totals"]["cost_usd"]
            grand["latency_s"] += record["totals"]["latency_s"]
            grand["wall_clock_s"] += record["totals"]["wall_clock_s"]
            grand["errors"] += record["totals"]["errors"]

    print(f"\nTotal: ${grand['cost_usd']:.4f}, {grand['wall_clock_s']:.1f}s wall "
          f"({grand['latency_s']:.1f}s summed), {grand['errors']} cluster errors")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

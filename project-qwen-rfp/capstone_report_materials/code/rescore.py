#!/usr/bin/env python3
"""Re-run evidence verification over saved results, without re-calling any model.

Quote checking is a moving target early on - every fix to it (page-spanning
tables, list linearisation) changes the groundedness numbers. Re-running the
models to pick those up would cost money and, worse, would mix a checker change
with fresh sampling noise. This re-verifies the stored quotes in place instead,
so a checker fix is applied identically to every model's existing results.

    ./.venv/bin/python rescore.py
"""
from __future__ import annotations

import json
from pathlib import Path

from rfpbench.document import Document
from rfpbench.runner import _check_evidence, summarise

ROOT = Path(__file__).parent


def main() -> int:
    results = sorted((ROOT / "results").rglob("*.json"))
    if not results:
        print("no results to rescore")
        return 1

    docs: dict = {}
    for path in results:
        record = json.loads(path.read_text())
        doc_path = record["doc_path"]
        if doc_path not in docs:
            if not Path(doc_path).exists():
                print(f"  SKIP {path.name}: source PDF missing ({doc_path})")
                continue
            docs[doc_path] = Document.load(doc_path)
        doc = docs[doc_path]

        before = record["summary"].get("groundedness")
        for key, answer in list(record["fields"].items()):
            # drop previous verdict so the check is recomputed from the quote alone
            answer.pop("_evidence", None)
            answer.pop("_field_type", None)
            record["fields"][key] = _check_evidence(doc, key, answer)
        record["summary"] = summarise(record)
        after = record["summary"].get("groundedness")

        path.write_text(json.dumps(record, indent=2, ensure_ascii=False))
        change = "" if before == after else f"   {before} -> {after}"
        print(f"  {path.parent.name:16s} {record['doc_id'][:44]:44s} "
              f"grounded={after}{change}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

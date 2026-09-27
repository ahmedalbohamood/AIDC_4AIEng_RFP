"""Prompt construction.

One template for all three models. Per-model prompt tuning would make the benchmark
measure prompt engineering effort rather than model capability, so the only thing
that varies is whether the document arrives as text or as page images.

The instructions are written as decision rules, not encouragement. "Absent is a
valid answer" is the single most important line here: without it models invent
plausible insurance minimums and deadlines for RFPs that never stated any, and
that failure mode is exactly what this benchmark is trying to measure.
"""
from __future__ import annotations

import json
from typing import List

from .document import Page, pages_as_text
from .fields import fields_in

SYSTEM = """You extract specific fields from government and enterprise RFP documents.

Rules:
1. Extract ONLY what the document explicitly states. Never infer, never complete a
   pattern, never carry a value over from a similar RFP you have seen.
2. If the document does not specify a field, set present=false and value=null - this
   means "NOT FOUND in the shown pages." An absent field is a correct and common
   answer, not a failure. A plausible guess dressed up as a real answer is wrong.
3. Every field you mark present=true MUST cite EXACTLY where it came from: the page
   number it appears on, and a verbatim quote copied character for character from
   that page. This citation is mandatory, not optional detail - it is what lets the
   answer be checked against the source at all. The quote is verified automatically
   against the source text; a citation that doesn't match is treated as fabricated.
4. Do not paraphrase inside quote. Copy the sentence(s) exactly as printed.
5. Page numbers are the PAGE markers given to you, not any page number printed in
   the document's own footer.
6. Where a value appears more than once (e.g. a deadline restated in an addendum),
   use the governing one and quote that occurrence.

--- WORKED EXAMPLE (a different RFP, shown once so you can calibrate depth and
    format - the document you are about to read is unrelated; do not reuse any
    value below) ---

Page 4 of that RFP reads: "The term of the agreement resulting from this RFP is to
be for a period of one (1) year, with options to extend the agreement on the same
terms and conditions for four (4) additional 1-year renewal periods for a total
term not to exceed five (5) years collectively."

Correct answer for a "contract_term" field there:
{"present": true, "value": "1-year initial term with options to extend for four
additional 1-year renewal periods, total term not to exceed 5 years", "quote": "The
term of the agreement resulting from this RFP is to be for a period of one (1)
year, with options to extend the agreement on the same terms and conditions for
four (4) additional 1-year renewal periods for a total term not to exceed five (5)
years collectively.", "page": 4}
Why: it reports BOTH the renewal structure AND the explicit 5-year total cap stated
in the same sentence. Stopping at "1 year + 4 renewals" and dropping the total-term
cap would have missed a fact sitting right inside the same quote.

Elsewhere, that RFP's rated-criteria table sums to 100% across five categories, but
no numeric minimum score or per-category cutoff is ever stated - only two unrelated
pass/fail gates exist (a technical-requirements check and a security precondition),
neither of which is a score.

Correct answer for "minimum_score_threshold" there: {"present": false, "value": null}
Why: inventing a plausible cutoff (e.g. "70%") because a scoring table exists
nearby would be a fabrication. Absent is the correct, common answer whenever the
document never actually writes a threshold down - do not manufacture one from a
scoring rubric that merely sums to 100%.
--- END WORKED EXAMPLE ---"""


def build_messages(cluster: str, pages: List[Page], modality: str,
                   doc_id: str, dpi: int = 150) -> list:
    """Build the chat messages for one cluster against selected pages."""
    field_block = "\n".join(
        f"- {f.key} ({f.label}): {f.guidance}" for f in fields_in(cluster)
    )
    page_list = ", ".join(str(p.number) for p in pages)

    instruction = (
        f"Document: {doc_id}\n"
        f"You are shown pages: {page_list}\n\n"
        f"Extract these fields:\n{field_block}\n\n"
        "Return JSON matching the required schema. Cite page numbers from the list "
        "above. If a field is not specified on these pages, set present=false rather "
        "than guessing from elsewhere."
    )

    if modality == "vision":
        content = [{"type": "text", "text": instruction}]
        for page in pages:
            # The label before each image is what lets the model cite a page at all;
            # without it, page numbers in the output are guesses.
            content.append({"type": "text", "text": f"--- PAGE {page.number} ---"})
            content.append({
                "type": "image_url",
                "image_url": {"url": page.image_data_url(dpi=dpi), "detail": "high"},
            })
        user_content = content
    else:
        user_content = instruction + "\n\n" + pages_as_text(pages)

    return [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user_content},
    ]


VERIFY_SYSTEM = """You are reviewing a first-draft extraction for completeness, not \
re-extracting from scratch. The draft was written by a model reading the same pages \
you are about to see - it is usually grounded and correctly-quoted, but under this \
benchmark's own measurement, its single most common failure is dropping a SECOND fact \
that sits right next to the one it already found (e.g. it states a base contract term \
but drops the stated maximum-term cap in the same sentence; it lists 3 of 8 required \
items from a list and stops).

Your only job: re-read the source pages yourself, and for each field, check whether \
the draft's value is missing anything the pages actually state that this field asks \
for. Add what's missing. Do not remove or contradict anything in the draft that is \
already correct - only fill gaps. If the draft is already complete for a field, \
return it unchanged."""


def build_verify_messages(cluster: str, pages: List[Page], modality: str,
                          doc_id: str, draft: dict, dpi: int = 150) -> list:
    """Second-pass messages: same pages, plus the first pass's own answer, asking
    specifically for missed facts rather than a fresh extraction. Building this as
    a genuinely separate call (not restructuring the first prompt to ask for both
    at once) matters - a model composing an answer and auditing it for
    completeness at the same time is doing two jobs in one pass; splitting them
    gives the second pass nothing to do BUT look for gaps."""
    field_block = "\n".join(
        f"- {f.key} ({f.label}): {f.guidance}" for f in fields_in(cluster)
    )
    page_list = ", ".join(str(p.number) for p in pages)

    instruction = (
        f"Document: {doc_id}\n"
        f"You are shown pages: {page_list}\n\n"
        f"Fields and what they mean:\n{field_block}\n\n"
        f"First-draft extraction (yours to complete, not replace):\n"
        f"{json.dumps(draft, ensure_ascii=False, indent=2)}\n\n"
        "Return the same JSON shape, corrected only where the source pages state a "
        "fact this field asks for that the draft omitted."
    )

    if modality == "vision":
        content = [{"type": "text", "text": instruction}]
        for page in pages:
            content.append({"type": "text", "text": f"--- PAGE {page.number} ---"})
            content.append({
                "type": "image_url",
                "image_url": {"url": page.image_data_url(dpi=dpi), "detail": "high"},
            })
        user_content = content
    else:
        user_content = instruction + "\n\n" + pages_as_text(pages)

    return [
        {"role": "system", "content": VERIFY_SYSTEM},
        {"role": "user", "content": user_content},
    ]

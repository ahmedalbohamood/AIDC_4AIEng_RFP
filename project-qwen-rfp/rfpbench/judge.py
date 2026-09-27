"""LLM-as-judge grading for free-text fields, as a replacement for fuzzy string match.

Tried first: embedding cosine similarity (see semantic.py, kept for reference).
Calibration against known-correct-paraphrase and known-wrong pairs showed the
ranges overlap too much to pick a threshold - generic embeddings cluster same-
domain RFP text together regardless of whether the specific stated fact is right
("General Liability, 2000000 USD" scored HIGHER against ground truth than a
genuinely correct but differently-worded ERP scope description). Embeddings are
good for topical retrieval, not for judging factual equivalence.

An LLM judge compares meaning directly: given the ground truth value, the field's
guidance, and the model's answer, does the answer state the same core fact,
partially, or not at all - the "nearly accurate should count" behaviour that
string/vector similarity can't give reliably. This is exactly the rubric grading
the project's own fields.py comments call out as future work for free-text fields.

Costs one gpt-4o call per (field, ground truth, answer) triple, cached to disk by
exact content hash so repeat grade.py runs are free.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel

CACHE_PATH = Path(__file__).parent.parent / ".judge_cache.json"
MODEL = "gpt-4o"

_cache: dict | None = None
_client = None


# Bumped whenever PROMPT or the Verdict schema changes meaningfully, so a prompt
# fix doesn't silently keep serving stale verdicts graded under the old logic -
# a real near-miss this caught (2026-09-21): PROMPT_VERSION was absent, so the
# fact-decomposition rewrite below would have been graded in from the cache key's
# perspective as "no change" (same model/label/guidance/gt/answer), and every
# already-cached verdict would keep returning under the OLD holistic-judgment
# logic it was written to replace, with no error and no visible sign it happened.
PROMPT_VERSION = "4"


class FactCheck(BaseModel):
    fact: str  # one distinct, independently-checkable claim pulled from ground truth
    status: Literal["present", "partial", "missing"]


class Verdict(BaseModel):
    facts_checked: list[FactCheck]
    verdict: Literal["correct", "partial", "wrong"]
    reason: str


def _load_cache() -> dict:
    global _cache
    if _cache is None:
        _cache = json.loads(CACHE_PATH.read_text()) if CACHE_PATH.exists() else {}
    return _cache


def _save_cache() -> None:
    CACHE_PATH.write_text(json.dumps(_cache))


def _key(label: str, guidance: str, gt: str, answer: str) -> str:
    return hashlib.sha256(f"{MODEL}:{PROMPT_VERSION}:{label}:{guidance}:{gt}:{answer}".encode()).hexdigest()


def _get_client():
    global _client
    if _client is None:
        from openai import OpenAI
        _client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _client


# Rewritten 2026-09-21 from a single holistic pass to explicit per-fact
# decomposition. The old version asked for one verdict straight from reading both
# values once - fine for a one-clause ground truth, but a multi-clause sentence
# ("no minimum years, BUT X is a scored criterion (Y pts): A, B, and C, with D
# meaning E not F") asks the model to hold every clause in its head at once while
# also composing a one-sentence justification, and it starts mixing up which
# specific detail belongs to which clause. Caught directly: graded a Medicine Hat
# RFP answer as wrong for "misrepresenting" a reference count the model's own
# text stated CORRECTLY, verbatim, sitting three lines above the verdict that
# contradicted it. Same fix already worked for LIST fields (llm_judge_list) -
# check each item independently instead of one impression of the whole list; this
# applies that to single free-text fields, which had the same failure mode inside
# one field instead of across several.
PROMPT = """You are grading whether a model's extracted answer for one field of an \
RFP document states the same facts as the ground truth answer, written by a human \
who read the source PDF directly.

Field: {label}
What this field means: {guidance}

Ground truth answer (the correct extraction):
{gt}

Model's answer (to be graded):
{answer}

Work in three steps.

STEP 1 - List the distinct checkable facts in the ground truth answer. A fact is \
one specific, independently-verifiable claim: a number, a named party, a named \
document or section, a condition, a scope boundary, an explicit "not X" \
clarification. A ground truth sentence with several clauses joined by commas, \
"and", "but", or parentheses usually contains SEVERAL separate facts, not one -
list each separately, including short or seemingly-minor ones.

STEP 2 - For EACH fact from step 1, re-read the model's answer's literal words \
(not your memory of its general shape) and mark it:
- "present": the model's answer states this exact fact, even reworded, reordered, \
or made MORE SPECIFIC than the ground truth's own wording (e.g. ground truth says \
"stakeholders" and the answer names the specific organization - that is the same \
fact stated precisely, not a deviation; a narrower true statement is still a match)
- "partial": the model's answer touches this fact's topic but a specific part of \
it - a number, a name, a qualifier - is actually WRONG, contradicted, or dropped \
entirely, not merely phrased with more or less specificity than the ground truth
- "missing": the model's answer says nothing corresponding to this fact

Check the model's answer's actual text against each fact one at a time. A wrong \
per-fact mark, made by comparing against a general impression instead of the \
literal words, is the single most common grading mistake here - double-check any \
mark of "partial" or "missing" against the quoted text before finalizing it.

STEP 3 - Derive the overall verdict from the step 2 results, not from a fresh \
holistic impression:
- "correct": all facts are "present", or only a minor/secondary one is not
- "partial": most facts are "present" but at least one significant fact (a \
number, a named party, a condition that changes what's verifiable) is "partial" \
or "missing"
- "wrong": most facts are "missing" or contradicted, or the answer is generic/ \
topic-only with no fact actually present

The verdict is decided ENTIRELY by step 2's per-fact results above. The model's \
answer containing MORE than the ground truth - extra true details, extra scope, \
extra context - is never itself a reason to mark a fact "partial" or to lower the \
verdict, even if you'd phrase the answer differently or think it's padded. A fact \
is "partial" only when something about THAT SPECIFIC FACT (not the rest of the \
answer) is wrong, vague, or missing - never because the answer also said other \
true things beyond it. If every ground truth fact is "present", the verdict is \
"correct" regardless of what else the answer contains.

Give a one-sentence reason naming the specific fact(s) that were missing or wrong, \
if any - not a restated impression of the whole answer, and never a complaint \
about extra correct content."""


def llm_judge(label: str, guidance: str, gt_value: str, answer_value: str) -> tuple[str, str]:
    gt, answer = str(gt_value), str(answer_value)
    cache = _load_cache()
    k = _key(label, guidance, gt, answer)
    if k in cache:
        v = cache[k]
        return v["verdict"], v["reason"]

    resp = _get_client().chat.completions.parse(
        model=MODEL,
        messages=[{"role": "user", "content": PROMPT.format(
            label=label, guidance=guidance, gt=gt, answer=answer)}],
        response_format=Verdict,
        temperature=0.0,
    )
    parsed = resp.choices[0].message.parsed
    # facts_checked is kept in the cache (not in the return tuple, to avoid
    # touching grade.py's interface) purely so a miss can be audited later by
    # reading .judge_cache.json directly - exactly the kind of per-fact trace
    # that caught the Medicine Hat bug in the first place.
    cache[k] = {
        "verdict": parsed.verdict,
        "reason": parsed.reason,
        "facts_checked": [f.model_dump() for f in parsed.facts_checked],
    }
    _save_cache()
    return parsed.verdict, parsed.reason


class ListCoverage(BaseModel):
    covered_fraction: float  # 0.0-1.0: share of ground-truth items substantively present
    reason: str


LIST_PROMPT = """You are grading a LIST-type field extracted from an RFP document. \
Ground truth is a human's own list of the distinct facts/requirements found in the \
source - THEIR CHOICE of how many items to split them into. A model may group, \
split, reorder, or word these completely differently and still be capturing the \
same underlying facts. Do not penalize different segmentation - judge only whether \
each ground-truth fact is substantively present somewhere in the model's answer.

Field: {label}
What this field means: {guidance}

Ground truth items ({n} total):
{gt_items}

Model's answer:
{answer}

For each ground truth item, decide if the model's answer captures that same fact: \
fully (counts as 1), partially - mentions the topic but drops a specific detail like \
a number, named party, or condition (counts as 0.5), or not at all (counts as 0).

Return covered_fraction = (sum of those per-item scores) / {n}, as a number between \
0 and 1. The model's answer containing EXTRA items or details beyond the ground \
truth list is never a reason to lower any item's score - score each ground-truth \
item only on whether it is itself present, never on what else the answer contains. \
Give a one-sentence reason naming what's missing, if anything."""


def llm_judge_list(label: str, guidance: str, gt_items: list[str], answer_value) -> tuple[float, str]:
    """Returns (covered_fraction 0-1, reason). Caller applies its own recall bands."""
    answer_str = json.dumps(answer_value) if not isinstance(answer_value, str) else answer_value
    gt_items_str = "\n".join(f"{i+1}. {item}" for i, item in enumerate(gt_items))
    cache = _load_cache()
    k = _key("LIST:" + label, guidance, gt_items_str, answer_str)
    if k in cache:
        v = cache[k]
        return v["covered_fraction"], v["reason"]

    resp = _get_client().chat.completions.parse(
        model=MODEL,
        messages=[{"role": "user", "content": LIST_PROMPT.format(
            label=label, guidance=guidance, n=len(gt_items),
            gt_items=gt_items_str, answer=answer_str)}],
        response_format=ListCoverage,
        temperature=0.0,
    )
    parsed = resp.choices[0].message.parsed
    frac = max(0.0, min(1.0, parsed.covered_fraction))
    cache[k] = {"covered_fraction": frac, "reason": parsed.reason}
    _save_cache()
    return frac, parsed.reason

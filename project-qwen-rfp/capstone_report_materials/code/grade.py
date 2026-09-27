#!/usr/bin/env python3
"""Grade saved model results against hand-written ground truth.

    ./.venv/bin/python grade.py                        # every doc that has ground truth
    ./.venv/bin/python grade.py --doc "CP-730126"       # one doc
    ./.venv/bin/python grade.py --verbose               # show every field, not just misses

This is the first real accuracy check in the project: everything before this
(groundedness, hallucination_rate) measured whether an answer was backed by a real
quote in the PDF, never whether the answer was actually correct. Ground truth here
was hand-written by reading the source PDF directly (see ground_truth/*.json for
the reasoning behind each answer, including the deliberate traps).
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

from dateutil import parser as dateparser
from dotenv import load_dotenv
from rapidfuzz import fuzz

from rfpbench.fields import BY_KEY
from rfpbench.judge import llm_judge, llm_judge_list

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")


def load_results(doc_id: str) -> dict:
    """{backend: field_answers} for one document, across every backend that ran it."""
    out = {}
    for backend_dir in sorted((ROOT / "results").iterdir()):
        if not backend_dir.is_dir():
            continue
        f = backend_dir / f"{doc_id}.json"
        if f.exists():
            out[backend_dir.name] = json.loads(f.read_text())["fields"]
    return out


def norm_text(s) -> str:
    return re.sub(r"\s+", " ", str(s)).strip().lower()


# Confirmed bug (2026-09-21): dateutil.parser.parse throws a hard ParserError on
# "H.MM AM/PM" (period instead of colon) - and several source RFPs in this corpus
# write their own deadline that way (e.g. Rocky View County's cover page literally
# says "2.00 PM MST Alberta Time"). A model that quotes the deadline verbatim from
# the document was therefore being marked WRONG for being byte-for-byte accurate.
# Also silence (not just tolerate) the UnknownTimezoneWarning noise for the North
# American abbreviations this corpus actually uses, so ambiguous but recognizable
# zone names don't clutter output - they don't affect grading since grade_field
# only ever compares .date(), never time-of-day or tzinfo.
_TZINFOS = {
    name: offset * 3600
    for name, offset in {
        "MST": -7, "MDT": -6, "MT": -7,
        "PST": -8, "PDT": -7, "PT": -8,
        "CST": -6, "CDT": -5, "CT": -6,
        "EST": -5, "EDT": -4, "ET": -5,
    }.items()
}


def _parse_date(s: str):
    # Normalize "H.MM" -> "H:MM" only in front of AM/PM so decimal numbers
    # elsewhere in the string (dollar amounts, section numbers) are untouched.
    s = re.sub(r"(\d{1,2})\.(\d{2})(\s*[AaPp][Mm])", r"\1:\2\3", s)
    return dateparser.parse(s, fuzzy=True, tzinfos=_TZINFOS)


def norm_list(v) -> set:
    """Set of item strings, so grading is order-independent."""
    items = []
    for item in v or []:
        if isinstance(item, dict):
            items.append(str(item.get("category") or item.get("coverage_type") or item))
        else:
            items.append(str(item))
    return {norm_text(i) for i in items if str(i).strip()}


def _has_real_content(v) -> bool:
    """True if v looks like actual extracted content rather than a null placeholder.
    Some structured outputs set present=false but still populate value with either
    real content (a self-contradiction worth rescuing) or a literal null-ish
    placeholder like "null" or ["null"] (not real content, correctly stays absent)."""
    if v is None:
        return False
    if isinstance(v, str):
        return v.strip().lower() not in ("", "null", "none", "n/a")
    if isinstance(v, list):
        return len(v) > 0 and any(_has_real_content(item) for item in v)
    if isinstance(v, dict):
        return len(v) > 0
    return True


def grade_field(spec, truth: dict, answer: dict | None) -> tuple[str, str]:
    """Returns (verdict, explanation). verdict in {correct, partial, wrong, missing}."""
    if answer is None:
        return "missing", "model produced no answer for this field at all"

    got_present = bool(answer.get("present"))
    want_present = bool(truth.get("present"))

    if not want_present:
        if not got_present:
            return "correct", "correctly absent"
        return "wrong", f"HALLUCINATED a value where none exists: {answer.get('value')!r}"

    rescued = False
    if not got_present:
        # Confirmed bug (2026-09-21), checked against raw results JSON: some vLLM
        # guided_json outputs (seen from qwen3.5-9b) set present=false while still
        # populating value with real, substantive content - a self-contradiction in
        # the model's own structured output, not truly an "I found nothing" answer.
        # One CP-730126 case had present=false but value containing several items
        # that verbatim-match ground truth's mandatory submission list - grading
        # that "wrong" throws away content the model actually got right. Rescue
        # only when value looks like real content, not a null placeholder (Olds
        # College's value=["null"] is NOT real content and stays correctly absent).
        if _has_real_content(answer.get("value")):
            rescued = True
        else:
            return "wrong", "model said absent, but the field is genuinely in the document"

    # both present (or rescued) -> compare values by type
    t, a = truth.get("value"), answer.get("value")
    verdict, why = _compare_values(spec, t, a, answer)
    if rescued:
        why = "[present=false but value had real content, graded anyway] " + why
    return verdict, why


def _compare_values(spec, t, a, answer: dict) -> tuple[str, str]:
    ftype = spec.type.value

    if ftype == "number" and isinstance(t, list):
        # minimum_score_threshold on EN_-_ERP_RFP_24.25.04 (and any field like it)
        # genuinely has more than one correct scalar answer - documented in that
        # ground truth's own note when it was written: the RFP states FOUR separate
        # per-category thresholds (e.g. 28/35 points = 80% functional fit, 21/30 =
        # 70% vendor demo) plus an 80% headline figure, with no single overall pass
        # score. A model answering 28 or 21 is reporting a real, correctly-quoted
        # threshold from the document, not a wrong number - grading it "wrong"
        # against only one of several valid representations was always a bug in
        # how strict equality was applied, not a grading-generosity choice.
        try:
            af = float(a)
            for candidate in t:
                if af == float(candidate):
                    return "correct", f"number matches accepted value {candidate!r} (of {t!r})"
            return "wrong", f"got {a!r}, want one of {t!r}"
        except (TypeError, ValueError):
            return "wrong", f"got non-numeric {a!r}, want one of {t!r}"

    if ftype == "datetime":
        if t is None:
            # A field can be genuinely present=true with no computable calendar
            # date - e.g. 02_Certification_Testing_Platform_and_Services_RFP's
            # questions_deadline is only ever stated as a relative rule ("not less
            # than five business days before the Closing Date"), never an absolute
            # date. There's nothing to date-parse here; every model that reports
            # present=true with a real, grounded quote about the actual rule has
            # correctly found the fact, so grade that instead of trying (and
            # failing) to parse GT's None as a date.
            return "correct", "no computable date in ground truth - present=true credited on quote/evidence alone"
        try:
            td = _parse_date(str(t))
            ad = _parse_date(str(a))
        except Exception:
            return "wrong", f"unparseable date: got {a!r}"
        if td.date() != ad.date():
            return "wrong", f"wrong date: got {a!r}, want {t!r}"
        # Some ground truth values deliberately carry no time-of-day (date only); if
        # the model invented a clock time the source never states, flag it. Bug fixed
        # 2026-09-20: this used to test whether the literal substring "time" appeared
        # in the ground truth VALUE string, which is true almost never - ISO datetimes
        # like '2025-04-29T14:00:00-04:00' contain no such substring, so every model
        # that correctly matched a ground truth value WITH a real time got downgraded
        # to "partial" for it. The actual signal is whether ground truth's own ISO
        # value encodes an explicit hour:minute (a literal 'T' followed by digits).
        # Bug fixed AGAIN 2026-09-25: that ISO-only check went back to being wrong
        # once a ground-truth author started writing plain-English dates with times
        # ('May 14, 2025, 2:00 PM MST') instead of ISO - the ISO regex never matches
        # plain English, so gt_has_time was False for every single date field in that
        # ground truth, and every model's correctly-extracted time got flagged as
        # invented, on every document. Now checks for a stated time in EITHER
        # format, not just ISO.
        raw = norm_text(answer.get("raw") or a)
        time_pattern = r"\d{1,2}\s*:\s*\d{2}|am\b|pm\b"
        gt_has_time = bool(re.search(r"T\d{2}:\d{2}", str(t))) or bool(re.search(time_pattern, str(t).lower()))
        if re.search(time_pattern, raw) and not gt_has_time:
            return "partial", f"right date, but INVENTED a time not in the source: {a!r}"
        return "correct", "date matches"

    if ftype == "number":
        try:
            if float(t) == float(a):
                return "correct", "number matches"
            return "wrong", f"got {a!r}, want {t!r}"
        except (TypeError, ValueError):
            return "wrong", f"got non-numeric {a!r}, want {t!r}"

    if ftype == "boolean":
        return ("correct", "matches") if bool(a) == bool(t) else ("wrong", f"got {a!r}, want {t!r}")

    if ftype == "contact":
        # Rewritten 2026-09-25: this used to split the ground truth on the first
        # comma and require that exact substring inside the model's answer -
        # written assuming GT always looks like "Name, Title, Org". A ground
        # truth written as a longer sentence with semicolons instead ("Jane Doe;
        # jane@x.ca. RFP communications must be initiated through...") has no
        # comma before the sentence, so the OLD code took the whole sentence as
        # "the name" and failed to find it in a clean structured answer - even
        # when the model's name and email were both exactly, verifiably correct.
        # Email is unambiguous and format-independent, so check that first; only
        # fall back to a name-token overlap check if the ground truth has none.
        blob = norm_text(json.dumps(answer))
        gt_text = str(t)
        email_match = re.search(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", gt_text)
        if email_match and norm_text(email_match.group(0)) in blob:
            return "correct", "email found"
        # Fall back to a name check: split on the first of , ; or . (whichever
        # comes first), not comma alone.
        cut = min((i for i in (gt_text.find(c) for c in ",;.") if i != -1), default=len(gt_text))
        want_name = norm_text(gt_text[:cut])
        if want_name and want_name in blob:
            return "correct", "name found"
        return "partial", f"expected {t!r} not clearly matched in {answer!r}"

    if ftype in ("list", "table"):
        if not t:
            return "correct", "empty list matches"
        # Fuzzy per-item match forces the model's answer to segment its items the
        # SAME way the ground-truth writer happened to - a model that merges two
        # ground-truth items into one, or splits one into two, or reorders/rewords,
        # gets penalized for a structural choice that was never actually graded
        # content. Field-type breakdown (2026-09-21) showed this: LIST fields
        # scored 39% correct vs TABLE fields' 74% on the exact same matching code,
        # because table rows (category+weight, coverage+amount) are structurally
        # constrained and leave little room for arbitrary segmentation disagreement
        # - list items don't have that constraint. An LLM judge that scores whether
        # each ground-truth FACT is present, independent of how the model grouped
        # or worded it, removes that penalty while still requiring real coverage.
        gt_items = t if isinstance(t, list) else [t]
        gt_item_strs = [json.dumps(i) if isinstance(i, dict) else str(i) for i in gt_items]
        try:
            recall, reason = llm_judge_list(spec.label, spec.guidance, gt_item_strs, a)
            note = f"llm-judge: coverage={recall:.0%} - {reason}"
        except Exception as exc:
            want, got = norm_list(t), norm_list(a)
            hits = sum(1 for w in want if any(fuzz.token_set_ratio(w, g) >= 65 for g in got))
            recall = hits / len(want) if want else 1.0
            note = f"[judge unavailable: {exc}] recall={recall:.0%} ({hits}/{len(want)} items)"
        if recall >= 0.8:
            return "correct", note
        if recall >= 0.4:
            return "partial", note
        return "wrong", note

    # free text - LLM-as-judge (compares meaning, not word overlap), with fuzzy
    # match as a fallback if the judge call fails (e.g. no API key/network).
    # Calibration (2026-09-21): tried embedding cosine similarity first - its
    # scores for known-correct-paraphrase pairs (0.52-0.79) overlapped too much
    # with known-wrong pairs (0.40-0.58) for any threshold to separate them (a
    # wrong-currency, wrong-coverage-type insurance answer scored HIGHER than a
    # genuinely correct differently-worded scope answer). An LLM judge that reads
    # both values and reasons about the actual claim does not have that problem.
    try:
        verdict, reason = llm_judge(spec.label, spec.guidance, str(t), str(a))
        return verdict, f"llm-judge: {reason}"
    except Exception as exc:
        score = fuzz.token_set_ratio(norm_text(t), norm_text(a))
        note = f"[judge unavailable: {exc}] "
        if score >= 70:
            return "correct", f"{note}similarity={score}"
        if score >= 40:
            return "partial", f"{note}similarity={score}"
        return "wrong", f"{note}similarity={score} - got {str(a)[:80]!r}"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--doc", help="substring filter on doc id")
    ap.add_argument("--exclude", action="append", default=[],
                    help="substring filter to drop doc ids (repeatable); use for docs "
                         "whose ground truth now appears verbatim in the system prompt "
                         "as a few-shot example, since their score is no longer a fair "
                         "test of extraction")
    ap.add_argument("--verbose", action="store_true", help="show every field, not just misses")
    args = ap.parse_args()

    gt_files = sorted((ROOT / "ground_truth").glob("*.json"))
    if args.doc:
        gt_files = [f for f in gt_files if args.doc.lower() in f.stem.lower()]
    for pattern in args.exclude:
        gt_files = [f for f in gt_files if pattern.lower() not in f.stem.lower()]
    if not gt_files:
        print("no ground truth files found (see ground_truth/*.json)")
        return 1

    tally = defaultdict(lambda: defaultdict(int))          # tally[backend][verdict]
    by_difficulty = defaultdict(lambda: defaultdict(int))  # by_difficulty[(backend,diff)][verdict]
    grounded_partial = defaultdict(int)                    # backend -> count of partials with a verified citation

    for gt_file in gt_files:
        gt = json.loads(gt_file.read_text())
        doc_id = gt["doc_id"]
        results = load_results(doc_id)
        if not results:
            print(f"[skip] no saved results for {doc_id!r}")
            continue

        print(f"\n{'='*100}\n{doc_id}\n{'='*100}")
        for key, truth in gt["fields"].items():
            spec = BY_KEY[key]
            diff = truth.get("difficulty", "medium")
            row_printed = False
            for backend, fields in results.items():
                answer = fields.get(key)
                verdict, why = grade_field(spec, truth, answer)
                tally[backend][verdict] += 1
                by_difficulty[(backend, diff)][verdict] += 1
                # "Grounded" credit (2026-09-25): a partial answer whose citation is
                # mechanically verified against the source - the model found the
                # right page and quoted it accurately, it just didn't capture every
                # sub-fact. Reported as a SEPARATE, clearly-labeled column, never
                # folded into "accuracy" itself - collapsing the two would mean the
                # score stops measuring completeness at all, and stops being
                # comparable to anything graded the strict way.
                if verdict == "partial" and answer and answer.get("_evidence", {}).get("status") == "verified":
                    grounded_partial[backend] += 1
                if args.verbose or verdict != "correct":
                    if not row_printed:
                        print(f"\n[{diff:6s}] {key}")
                        if truth.get("note"):
                            print(f"          note: {truth['note'][:110]}")
                        row_printed = True
                    mark = {"correct": "OK", "partial": "~~", "wrong": "XX", "missing": "??"}[verdict]
                    print(f"    {mark}  {backend:20s} {why}")

    print(f"\n{'='*100}\nSCORE by model\n{'='*100}")
    print(f"{'backend':22s} {'correct':>8s} {'partial':>8s} {'wrong':>8s} {'missing':>8s} "
          f"{'accuracy':>9s} {'+grounded':>10s}")
    for backend, counts in sorted(tally.items()):
        total = sum(counts.values())
        acc = counts["correct"] / total if total else 0
        # Strict accuracy is the real number. "+grounded" is a SEPARATE, more lenient
        # view that also credits a partial answer whose citation checks out against
        # the source - shown side by side, never merged into "accuracy" above.
        grounded_acc = (counts["correct"] + grounded_partial[backend]) / total if total else 0
        print(f"{backend:22s} {counts['correct']:8d} {counts['partial']:8d} "
              f"{counts['wrong']:8d} {counts['missing']:8d} {acc:9.1%} {grounded_acc:10.1%}")

    print(f"\n{'='*100}\nSCORE by difficulty\n{'='*100}")
    print(f"{'backend':22s} {'difficulty':10s} {'correct':>8s} {'partial':>8s} {'wrong':>8s} {'accuracy':>9s}")
    for (backend, diff), counts in sorted(by_difficulty.items(), key=lambda x: (x[0][0], x[0][1])):
        total = sum(counts.values())
        acc = counts["correct"] / total if total else 0
        print(f"{backend:22s} {diff:10s} {counts['correct']:8d} {counts['partial']:8d} "
              f"{counts['wrong']:8d} {acc:9.1%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

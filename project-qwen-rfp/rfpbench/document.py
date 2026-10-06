"""PDF loading and page selection.

RFPs run 50-200 pages. A page image costs ~1-2k vision tokens, so stuffing a whole
document into a vision model is not an option; even for text models, a 200-page RFP
against a 4-bit 70B on one A6000 will not fit. So we select candidate pages per
field cluster and send only those.

Selection is deliberately simple and swappable (keyword scoring over page text). If
it turns out to be the bottleneck, replace `select_pages` with embeddings - but
measure first, because on RFPs the section headings are usually literal.
"""
from __future__ import annotations

import base64
import json
import math
import os
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import pymupdf as fitz

from .fields import FieldSpec, FieldType, fields_in, keywords_for

# Local, CPU-only embedding model (no API key, no external service) - swapped in
# when neither the OpenAI, DeepSeek, nor Claude keys available to this project
# offer an embeddings endpoint. Weights cache under fastembed's default HF cache
# dir on first use (~130MB download).
EMBED_MODEL = "BAAI/bge-small-en-v1.5"

_embed_model = None
_query_embed_cache: Dict[str, List[float]] = {}


def _model():
    global _embed_model
    if _embed_model is None:
        from fastembed import TextEmbedding
        _embed_model = TextEmbedding(model_name=EMBED_MODEL)
    return _embed_model


def _embed(texts: List[str]) -> List[List[float]]:
    """Raw embeddings, one per input text, same order. Caller handles caching."""
    return [vec.tolist() for vec in _model().embed(texts)]


def _cosine(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb) if na and nb else 0.0


def _field_query_embedding(spec: FieldSpec) -> List[float]:
    """The field's label+guidance IS the retrieval query - it already describes,
    in plain language, what a matching page looks like. Cached globally since
    fields never change within a process."""
    if spec.key not in _query_embed_cache:
        _query_embed_cache[spec.key] = _embed([f"{spec.label}. {spec.guidance}"])[0]
    return _query_embed_cache[spec.key]


DOCLING_CACHE_DIR = Path(__file__).parent.parent / ".docling_cache"


def _docling_pages(doc_id: str, path: Path) -> Dict[int, str]:
    """Per-page markdown via Docling instead of PyMuPDF's flattened text - Docling
    keeps table columns as real markdown tables, where PyMuPDF's get_text("text")
    runs a table's cells together into one unstructured line. Cached to disk
    (~2s/page, CPU-only since the GPU is busy with vLLM) since Document.load can
    be called repeatedly across a benchmark run for the same doc."""
    cache_file = DOCLING_CACHE_DIR / f"{doc_id}.json"
    if cache_file.exists():
        return {int(k): v for k, v in json.loads(cache_file.read_text()).items()}

    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.datamodel.base_models import InputFormat

    opts = PdfPipelineOptions()
    opts.do_ocr = False          # every doc in this corpus has a real text layer
    opts.do_table_structure = True
    conv = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)})
    result = conv.convert(str(path))
    n = result.document.num_pages()
    pages = {i: result.document.export_to_markdown(page_no=i) for i in range(1, n + 1)}

    DOCLING_CACHE_DIR.mkdir(exist_ok=True)
    cache_file.write_text(json.dumps(pages))
    return pages


@dataclass
class Page:
    number: int          # 1-based, matches what we ask the model to cite
    text: str
    _doc: "Document"

    def image_data_url(self, dpi: int = 150) -> str:
        return self._doc.render_page(self.number, dpi=dpi)


@dataclass
class Document:
    doc_id: str
    path: Path
    pages: List[Page]
    _table_cache: Dict[int, bool] = field(default_factory=dict, repr=False)
    _page_embed_cache: Dict[int, List[float]] = field(default_factory=dict, repr=False)

    @classmethod
    def load(cls, path: str | Path, use_docling: bool = False) -> "Document":
        path = Path(path)
        doc = cls(doc_id=path.stem, path=path, pages=[])
        with fitz.open(path) as pdf:
            n_pages = pdf.page_count
            pymupdf_text = {i: pdf[i - 1].get_text("text") for i in range(1, n_pages + 1)}

        docling_text = _docling_pages(doc.doc_id, path) if use_docling else {}
        for i in range(1, n_pages + 1):
            # Docling occasionally returns an empty page (e.g. a pure-image page it
            # can't parse without OCR); fall back to PyMuPDF's text rather than
            # silently showing the model nothing for that page.
            text = docling_text.get(i) or pymupdf_text[i]
            doc.pages.append(Page(number=i, text=text, _doc=doc))
        return doc

    @property
    def n_pages(self) -> int:
        return len(self.pages)

    @property
    def full_text(self) -> str:
        return "\n".join(p.text for p in self.pages)

    def page(self, number: int) -> Optional[Page]:
        if 1 <= number <= len(self.pages):
            return self.pages[number - 1]
        return None

    def render_page(self, number: int, dpi: int = 150) -> str:
        """Page as a data: URL PNG, for vision models."""
        with fitz.open(self.path) as pdf:
            pix = pdf[number - 1].get_pixmap(dpi=dpi)
            png = pix.tobytes("png")
        return "data:image/png;base64," + base64.b64encode(png).decode()

    def has_table(self, number: int) -> bool:
        """Whether PyMuPDF's table detector finds a real table on this page.

        Cached per-document because it re-opens the PDF (find_tables needs the
        live fitz.Page, which Page.text doesn't keep around) and gets called
        repeatedly while walking continuation pages in select_pages.
        """
        if number not in self._table_cache:
            try:
                with fitz.open(self.path) as pdf:
                    self._table_cache[number] = len(pdf[number - 1].find_tables().tables) > 0
            except Exception:
                self._table_cache[number] = False
        return self._table_cache[number]

    def page_embeddings(self) -> Dict[int, List[float]]:
        """Embed every page once, in a single batch call, cached for the life of
        this Document. Empty pages are skipped (no query is ever meaningfully
        close to nothing). Returns {} if no embeddings-capable key is configured -
        callers fall back to keyword-only ranking (see _score_pages_hybrid)."""
        if not self._page_embed_cache:
            numbered = [(p.number, p.text.strip()) for p in self.pages if p.text.strip()]
            if numbered:
                try:
                    vectors = _embed([f"Page {n}: {text[:8000]}" for n, text in numbered])
                except Exception:
                    return {}
                for (n, _), vec in zip(numbered, vectors):
                    self._page_embed_cache[n] = vec
        return self._page_embed_cache

    def is_text_extractable(self, min_chars_per_page: int = 100) -> bool:
        """False for scanned PDFs, where the text layer is empty or near-empty.

        Matters a lot: if this is False, the text-only models are being fed nothing
        and the comparison is meaningless without OCR first.
        """
        if not self.pages:
            return False
        non_empty = sum(1 for p in self.pages if len(p.text.strip()) >= min_chars_per_page)
        return non_empty >= 0.5 * len(self.pages)


_WORD = re.compile(r"[a-z0-9@%$.]+")


def _score_pages(doc: Document, keywords) -> List[tuple]:
    """(score, page) for pages matching any keyword, best first."""
    keywords = [kw.lower() for kw in keywords]
    scored = []
    for page in doc.pages:
        text = page.text.lower()
        if not text.strip():
            continue
        score = 0.0
        for kw in keywords:
            hits = text.count(kw)
            if hits:
                # Multi-word keywords are far more discriminative than single tokens.
                weight = 3.0 if " " in kw else 1.0
                score += weight * min(hits, 5)
        if score:
            scored.append((score, page))
    scored.sort(key=lambda sp: (-sp[0], sp[1].number))
    return scored


def _score_pages_embedding(doc: Document, spec: FieldSpec) -> List[tuple]:
    """(similarity, page) ranked by semantic closeness to the field's own
    label+guidance, best first - unlike _score_pages, this catches a page that
    describes the right content in different words than the keyword list
    anticipated (a real, not hypothetical, gap: keyword scoring only fires on
    literal string matches, so a page saying 'the vendor must carry two million
    in coverage' is invisible to it if the keyword list doesn't have that exact
    phrasing). Returns [] if no embeddings-capable key is configured."""
    try:
        query = _field_query_embedding(spec)
    except Exception:
        return []
    pages = doc.page_embeddings()
    if not pages:
        return []
    scored = [(_cosine(query, vec), doc.page(n)) for n, vec in pages.items()]
    scored.sort(key=lambda sp: (-sp[0], sp[1].number))
    return scored


def _score_pages_hybrid(doc: Document, spec: FieldSpec) -> List[tuple]:
    """(fused_score, page) combining embedding-similarity rank and keyword-match
    rank via reciprocal rank fusion, best first.

    Added 2026-09-22, after an oracle-pages test (feeding the model the exact
    pages the ground truth cites, bypassing retrieval) confirmed retrieval is a
    real, large cause of lost accuracy (+23.5 points on AB-2026-05648 - 41.2% ->
    64.7% - just from perfect page selection). Embedding similarity alone still
    misses a page that states the right fact in exact, distinctive vocabulary
    (e.g. 'Schedule B', 'Mandatory Requirements') if that exact phrase happens to
    embed a bit further from the field's own label+guidance text than some
    other, less-relevant page. Keyword scoring alone misses paraphrases (the
    original problem fix #1 solved). Combining by RANK rather than raw score
    avoids the scale-mismatch of cosine similarity (a tight 0.2-0.4 band) vs
    keyword hit counts (unbounded) - reciprocal rank fusion (1/(60+rank), the
    standard constant from the original RRF paper) is scale-free by
    construction: a page that's #1 on either signal contributes strongly, and a
    page ranked decently on BOTH signals can outrank a page that's #1 on only
    one.
    """
    emb_ranked = _score_pages_embedding(doc, spec)
    kw_ranked = _score_pages(doc, spec.keywords)
    emb_rank = {page.number: r for r, (_, page) in enumerate(emb_ranked)}
    kw_rank = {page.number: r for r, (_, page) in enumerate(kw_ranked)}
    all_pages = {p.number: p for p in doc.pages}
    fused = []
    for n, page in all_pages.items():
        if n not in emb_rank and n not in kw_rank:
            continue
        score = 0.0
        if n in emb_rank:
            score += 1.0 / (60 + emb_rank[n])
        if n in kw_rank:
            score += 1.0 / (60 + kw_rank[n])
        fused.append((score, page))
    fused.sort(key=lambda sp: (-sp[0], sp[1].number))
    return fused


def select_pages(doc: Document, cluster: str, k: int = 8, per_field: int = 5,
                 max_pages: Optional[int] = None) -> List[Page]:
    """Pages for a cluster, with a guaranteed allocation per field.

    Scoring the cluster's keywords as one pool lets a field with many common
    keywords crowd out a field with few. Measured on a real 39-page RFP: the
    `commercial` cluster (7 fields) returned pages carrying 'pricing' and
    'references' while the pages carrying the insurance schedule never made the
    cut, so every model correctly answered "absent" to a question whose answer it
    was never shown. That is a retrieval bug masquerading as a model failure, and
    it would have biased all three models identically.

    So: take each field's own top pages first, then spend whatever budget is left
    on the cluster-wide ranking. The first two pages are always pinned - deadlines,
    contact and submission method live there more often than keywords suggest.

    per_field raised 3->5 (2026-09-21): confirmed root cause of a universal
    failure - every model tested (gpt-4o, k2, qwen3.5, qwen3-vl-32b, gpt-5.5)
    missed data_security_requirements on RFP-2026-8-PR-CASCADE, and it turned out
    page 3 (the answer) was simply never shown to any of them. Its embedding
    score for that field (0.285) was a near-miss, 5th place behind a tight
    0.272-0.306 band of other pages - the answer is one generic sentence with
    none of the usual security vocabulary, so no single field's top-3 caught it,
    and by the time step 3's cluster-wide fallback ran, step 1 had already used
    the whole (even scaled) k budget. Widening the per-field net directly fixes
    a near-miss like this without the earlier padding experiment's failure mode
    (that one added neighbour PAGES with no cap; this raises how many of a
    field's OWN top-ranked pages are kept, which is bounded by the number of
    fields in the cluster regardless of document length).
    """
    chosen = {}
    priority = {}   # page number -> best (lowest) rank seen across all fields' rankings

    # Scale the budget by how many fields actually share this cluster (2026-09-21).
    # Found via a real regression: `commercial` has 7 fields, so step 1 alone can
    # fill all of k=8 before step 3's cluster-wide fallback - which is where a page
    # a field needs but whose own top-N ranking narrowly misses, like
    # data_security_requirements's answer on page 7 of
    # 04_Data_Centre_Download_Integration_Services_RFP - actually gets pulled in.
    # Editing a neighbouring field's guidance (which also changes ITS embedding
    # query under fix #1) shifted which pages filled step 1's slots first, starving
    # step 3 of room and silently dropping page 7. A fixed k=8 was tuned when
    # clusters were smaller; scaling it means a small cluster's budget doesn't
    # grow for no reason, but a big one always has fallback headroom left.
    n_fields = len(fields_in(cluster))
    k = max(k, n_fields + 5)

    # 1. per-field guarantee: no field can be starved by a noisier neighbour.
    # Hybrid rank fusion (fix #2, 2026-09-22) replaces pure embedding similarity
    # here - embeddings alone (fix #1, 2026-09-21) fixed the paraphrase-blind
    # spot of keyword-only scoring, but an oracle-pages test showed real
    # accuracy is still being lost to pages that rank just below cutoff on
    # embedding similarity despite containing an exact, distinctive phrase
    # (e.g. 'Schedule B') keyword scoring would have caught outright. Cluster-
    # wide fallback (step 3, below) still uses plain keywords since it's just
    # spending leftover budget, not the primary retrieval signal.
    for spec in fields_in(cluster):
        top_hits = _score_pages_hybrid(doc, spec)[:per_field]
        for rank, (_, page) in enumerate(top_hits):
            chosen.setdefault(page.number, page)
            priority[page.number] = min(priority.get(page.number, 999), rank)

        # TABLE fields (evaluation_criteria, insurance_requirements) commonly run
        # onto a second/third page with no repeated heading, so keyword scoring
        # alone stops at page 1 of the table - confirmed on City of Medicine Hat's
        # evaluation_criteria (p24-26): the model only ever saw p24, correctly
        # extracted the one row on it, and scored 20% because the other four rows
        # and the Stage 2 total were never shown. Unlike the reverted 2026-09-21
        # blanket-padding attempt, this only walks forward from a page keyword
        # scoring ALREADY picked, and only while PyMuPDF's table detector confirms
        # the next page is really still a table (capped at 2 extra pages) - a
        # whole-document table scan was tried first and rejected as too noisy
        # (18 "table" pages out of 57 on one doc, mostly false positives on form
        # fields), so this stays targeted rather than scanning every page.
        if spec.type == FieldType.TABLE and top_hits:
            start = top_hits[0][1].number
            if doc.has_table(start):
                n = start
                for _ in range(2):
                    n += 1
                    if n > doc.n_pages or not doc.has_table(n):
                        break
                    chosen.setdefault(n, doc.pages[n - 1])

    # Tried and reverted (2026-09-21): padding each per-field hit with neighbour
    # pages (to catch a list/section that continues past the page where its
    # keywords score highest - confirmed real on the Olds College LMS RFP, whose
    # Technical Requirements list starts on p20 but continues through p22 with no
    # repeated heading for keyword scoring to find on those later pages). It did
    # fix that exact case. But measured across the full 3-doc/2-model test it
    # LOST net (-7: 6 improved, 83 flat, 13 worse) against doing nothing, and lost
    # worse than full-text mode's own +3. Root cause: unpadded, no cap on how many
    # pages padding could add, it grew the `commercial` cluster (7 fields) to 36 of
    # 38 pages on that doc; with that much source text to synthesize, the model's
    # combined answer for all 7 fields overflowed the fixed 2048-token completion
    # budget and the JSON was cut off mid-string - `ok: False, error: "unparseable
    # JSON: Unterminated string..."` - which drops EVERY field in that cluster to
    # missing, not just the one padding was trying to help. A future attempt at
    # this needs either a hard cap on how many pages padding can add, or a
    # completion-budget check that raises max_tokens (or drops padding) when the
    # padded page count grows past some threshold - shipping neither, this was a
    # net loss and was removed rather than left in a regressed state.

    # 2. pinned front matter
    for page in doc.pages[:2]:
        chosen.setdefault(page.number, page)

    # 3. spend any remaining budget on the cluster-wide ranking.
    # Bug fixed 2026-09-22: pages added here never got a `priority` entry (only
    # step 1's per-field ranking set one), so they silently defaulted to the
    # worst rank (999) and were always the first cut whenever max_pages kicked
    # in below - regardless of how relevant they actually were. Confirmed on
    # AB-2026-05648-197-2027 RFP Learning Management System: page 21 (the answer
    # to two fields) reached `chosen` fine through this step, then got trimmed
    # by max_pages purely because of the missing priority, not low relevance.
    if len(chosen) < k:
        for rank, (_, page) in enumerate(_score_pages(doc, keywords_for(cluster))):
            if len(chosen) >= k:
                break
            if page.number not in chosen:
                chosen[page.number] = page
                priority[page.number] = min(priority.get(page.number, 999), rank)

    # 4. single-page gap fill (2026-09-22): confirmed real on
    # AB-2026-05648-197-2027 RFP Learning Management System - page 21 (Technical
    # Requirement #4 Security + Cloud-Based System, the answer to two fields)
    # narrowly missed every field's own top-N ranking, but pages 20 AND 22 both
    # made the cut. A page directly between two independently-selected pages is
    # very likely part of the same section a keyword/embedding ranking just
    # split across its neighbours - unlike the reverted 2026-09-21 padding
    # experiment (which added neighbours to every hit, unbounded), this only
    # fills an isolated single-page hole and can add at most one page per gap.
    gap_filled = set()
    for n in list(chosen):
        gap = n + 1
        if gap not in chosen and (gap + 1) in chosen and doc.page(gap):
            chosen[gap] = doc.page(gap)
            gap_filled.add(gap)

    # max_pages (2026-09-21): vision backends pay ~1-2k tokens PER PAGE IMAGE,
    # unlike text backends where more pages is comparatively cheap - confirmed by
    # a real crash: on 27-39 page RFPs, the `commercial` cluster's now-widened
    # per-field net (raised 3->5 above) selected up to 20 pages, and 4 of 5 docs
    # in one run 400'd with "Input length exceeds model's maximum context length"
    # on qwen3-vl-32b - a context overflow the retry/salvage logic in backends.py
    # doesn't even catch, since it only retries on JSON-parse failure, not on a
    # request that never got a response at all. Rather than cap per_field back
    # down (which would reintroduce the near-miss retrieval bug it fixed), trim
    # by actual relevance here: pinned front pages always survive, and beyond
    # that the pages with the best (lowest) rank across every field's own ranking
    # are kept first - this is a real relevance-based cut, not an arbitrary
    # page-number truncation.
    if max_pages and len(chosen) > max_pages:
        # Gap-filled pages are protected the same as pinned front matter (2026-09-22):
        # sandwiched between two independently-selected pages is a stronger signal
        # than an ordinary borderline ranking, so a priority-based cut shouldn't be
        # allowed to undo the gap-fill that just confirmed it.
        pinned = [n for n in chosen if n <= 2 or n in gap_filled]
        rest = sorted((n for n in chosen if n not in pinned), key=lambda n: priority.get(n, 999))
        keep = set(pinned) | set(rest[:max(0, max_pages - len(pinned))])
        chosen = {n: p for n, p in chosen.items() if n in keep}

    return [chosen[n] for n in sorted(chosen)]


def pages_as_text(pages: List[Page], max_chars_per_page: int = 12000) -> str:
    """Page-delimited text block. The delimiters are load-bearing: the model has to
    cite a page number, and it can only do that if it can see where pages break."""
    parts = []
    for p in pages:
        body = p.text.strip()
        if len(body) > max_chars_per_page:
            body = body[:max_chars_per_page] + "\n[... page truncated ...]"
        parts.append(f"===== PAGE {p.number} =====\n{body}")
    return "\n\n".join(parts)


def find_quote(doc: Document, quote: str, claimed_page: Optional[int]) -> dict:
    """Verify a model's quote against the source.

    Returns which page the quote is actually on, so we can distinguish three very
    different failures: a clean hit, a real quote attributed to the wrong page
    (sloppy but grounded), and a quote that appears nowhere (fabricated).
    """
    from rapidfuzz import fuzz

    result = {"found": False, "exact": False, "found_on_page": None, "best_score": 0.0,
              "spans_pages": False}
    if not quote or not quote.strip():
        return result

    needle = _norm(quote)
    if len(needle) < 12:          # too short to be evidence of anything
        return result

    # Long quotes are usually tables or bulleted lists. PDF text extraction does not
    # linearise those consistently - rows come out in column order, or with cells
    # reordered - so a contiguous alignment against the page fails even when every
    # cell is present. Measured on a real RFP: a correctly extracted evaluation
    # table scored partial_ratio=66 against the page it was copied from. Requiring
    # contiguity would mark correct table extraction as fabrication, and would do it
    # hardest to whichever model handles tables best. So for long quotes, verify by
    # segment coverage instead: how much of the quote is findable on the page, in
    # any order.
    # A literal ellipsis is the model explicitly marking "I skipped content here" -
    # some backends do this even on short quotes (Llama-70B: a 230-char quote
    # stitching two table cells across a gap, correctly, but scored 76.9 because it
    # was under the 300-char length gate and never got segmented at all). The
    # marker itself is a stronger signal than length, so it earns segment mode on
    # its own regardless of quote length.
    segments = _segments(quote) if len(needle) > 300 or "..." in quote or "…" in quote else []

    for page in doc.pages:
        hay = _norm(page.text)
        if not hay:
            continue

        if needle in hay:
            result.update(found=True, exact=True, found_on_page=page.number, best_score=100.0)
            if claimed_page == page.number:
                return result
            continue

        score = fuzz.partial_ratio(needle, hay)
        if segments:
            hits = sum(1 for seg in segments if fuzz.partial_ratio(seg, hay) >= 88)
            coverage = 100.0 * hits / len(segments)
            score = max(score, coverage)

        if score > result["best_score"]:
            result["best_score"] = score
            if score >= 90 and not result["found"]:
                result.update(found=True, exact=False, found_on_page=page.number)

    # A long table or requirements list routinely runs across a page break, and then
    # no single page contains all of it. Measured: an evaluation-criteria table that
    # was 51% on page 8 and 48% on page 9 - fully grounded, but rejected by any
    # per-page check. So retry segment coverage over adjacent page pairs.
    if segments and not result["found"]:
        for i in range(len(doc.pages) - 1):
            window = _norm(doc.pages[i].text) + " " + _norm(doc.pages[i + 1].text)
            if not window.strip():
                continue
            hits = sum(1 for seg in segments if fuzz.partial_ratio(seg, window) >= 88)
            coverage = 100.0 * hits / len(segments)
            if coverage > result["best_score"]:
                result["best_score"] = coverage
            if coverage >= 90:
                # Attribute to whichever page of the pair the quote starts on.
                first = segments[0]
                start = doc.pages[i].number
                if fuzz.partial_ratio(first, _norm(doc.pages[i + 1].text)) >= 88 and \
                   fuzz.partial_ratio(first, _norm(doc.pages[i].text)) < 88:
                    start = doc.pages[i + 1].number
                result.update(found=True, exact=False, found_on_page=start, spans_pages=True)
                break

    return result


def _segments(quote: str, min_len: int = 18) -> list:
    """Split a quote into independently checkable pieces (table rows, list items,
    sentences).

    Splitting only on newlines and double spaces is not enough: a model that
    stitches two separate passages of the document into one flowing quote produces
    a single blob that matches nothing contiguously, and scores as fabricated.
    Measured: a Qwen3-VL quote joining two real bullet points from the same page
    scored 75.7 as one segment and 100 once split. So also break on sentence
    boundaries - punctuation followed by whitespace and a capital - which leaves
    decimals and abbreviations like 'U.S.' intact. And break on a literal ellipsis:
    Llama-70B stitched a table's category name and its percentage across a gap
    with an explicit "..." marker (a correct, honest transcription of a table PDF
    text extraction had already scattered) - split on the model's own marker
    rather than trying to guess the gap's shape.
    """
    raw = re.split(r"[\n;]+|(?<=[.:!?])\s+(?=[A-Z(])|\.\.\.+|…", quote)
    return [s for s in (_norm(p) for p in raw) if len(s) >= min_len]


def _norm(s: str) -> str:
    """Normalise text for quote matching.

    Leader runs (the dots in 'Cost Proposal ......... 20 points') are collapsed
    because their length is not content, and getting it wrong penalises exactly
    one class of model. Measured on the synthetic RFP, where the ground truth is
    known: Qwen3-VL transcribed a 19-dot leader as 19 dots where the PDF had 20,
    scoring 87.6 against an 88 threshold - a correct table extraction recorded as
    a fabrication, purely because a vision model reads dots off pixels while text
    extraction copies the exact run. Same reason underscores and middle dots are
    folded here.

    NFKC also matters here, and separately: a PDF-embedded equation ('(price
    threshold / proponent's price) x weighting = ...') extracted as real text, not
    an image - but its variable names were typeset in Unicode Mathematical Italic
    codepoints (U+1D44E block), which LOOK identical to plain letters but are
    different characters. Qwen3.5-9B read it and, reasonably, wrote its quote back
    in plain ASCII; the raw comparison then saw zero character overlap between
    'price' and its mathematical-italic twin and scored a correct, real quote as
    fabricated at 52.6. NFKC decomposes the math-italic block back to plain Latin
    letters. It does not touch 'ᇱ' - a Hangul Jamo codepoint some equation
    renderer reused to draw a stylised apostrophe - so that one is folded in
    explicitly.
    """
    s = unicodedata.normalize("NFKC", s).replace("ᆱ", "'")
    s = re.sub(r"[.·•_‐-―\-]{3,}", " ", s)
    return re.sub(r"\s+", " ", s).strip().lower()

"""HTTP API for the AI RFP System Interface frontend.

Extraction runs on our own chosen local model (k2-horizon-7b, see the benchmark
this pipeline was picked from). Chat/RAG stays on OpenAI per instruction - it
reuses the same hybrid keyword+embedding retrieval already built and tested in
document.py, just against a free-text question instead of a fixed field spec.

    ./.venv/bin/uvicorn server:app --host 0.0.0.0 --port 8420 --reload
"""
from __future__ import annotations

import os
import threading
import time
import uuid
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env")

from dataclasses import replace as dataclass_replace
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Literal

from rfpbench.backends import default_backends
from rfpbench.document import Document, _cosine, _embed, _score_pages, find_quote, pages_as_text
from rfpbench.fields import BY_KEY, FIELDS
from rfpbench.runner import run_document
from rfpbench.schema import _inline_required

UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

EXTRACT_BACKEND_KEY = "k2-horizon-7b"  # the model this project's benchmark picked

app = FastAPI(title="AI RFP System Interface API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev only - tighten before any real deployment
    allow_methods=["*"],
    allow_headers=["*"],
)
Instrumentator().instrument(app).expose(app)  # GET /metrics - request counts, latency histograms

# ── Job store (in-memory; fine for a single-process dev server) ────────────────

JOBS: dict[str, dict] = {}
# Defaults to the local dev vLLM port; the ahmed-namespace deployment overrides
# this to the in-cluster Service DNS name (http://k2-vllm:8000/v1) via env var.
_backends = default_backends(vllm_url=os.environ.get("VLLM_URL", "http://localhost:8100/v1"))

# Same model, separate Backend instance: the agent reads a whole document in one
# call and can surface many verbose findings, so it needs more output room than
# the 3072-token budget the 17-field extraction clusters use.
_agent_backend = dataclass_replace(_backends[EXTRACT_BACKEND_KEY], max_tokens=6144)


def _run_extraction(document_id: str, pdf_path: Path) -> None:
    job = JOBS[document_id]
    try:
        job["stage"] = "Reading document"
        doc = Document.load(pdf_path)
        job["n_clusters_done"] = 0
        job["n_clusters_total"] = 6
        job["stage"] = "Extracting fields"

        backend = _backends[EXTRACT_BACKEND_KEY]
        record = run_document(doc, backend, verbose=False)

        job["fields"] = record["fields"]
        job["page_count"] = doc.n_pages
        job["stage"] = "Complete"
        job["progress"] = 100
        job["done"] = True
    except Exception as exc:  # surfaced to the frontend via status.error
        job["error"] = str(exc)
        job["done"] = True
        job["progress"] = 100


class UploadResponseModel(BaseModel):
    documentId: str
    fileNames: list[str]
    totalBytes: int


@app.post("/documents", response_model=UploadResponseModel)
async def upload_documents(files: list[UploadFile] = File(...)):
    if not files:
        raise HTTPException(400, "no files uploaded")
    document_id = f"doc_{uuid.uuid4().hex[:12]}"
    doc_dir = UPLOAD_DIR / document_id
    doc_dir.mkdir(parents=True, exist_ok=True)

    total_bytes = 0
    saved_names = []
    first_path: Optional[Path] = None
    for f in files:
        content = await f.read()
        total_bytes += len(content)
        dest = doc_dir / f.filename
        dest.write_bytes(content)
        saved_names.append(f.filename)
        if first_path is None and f.filename.lower().endswith(".pdf"):
            first_path = dest

    if first_path is None:
        raise HTTPException(400, "no PDF among the uploaded files")

    JOBS[document_id] = {
        "documentId": document_id,
        "pdf_path": first_path,
        "progress": 0,
        "stage": "Queued",
        "done": False,
        "error": None,
        "fields": None,
        "page_count": None,
    }
    threading.Thread(target=_run_extraction, args=(document_id, first_path), daemon=True).start()

    return UploadResponseModel(documentId=document_id, fileNames=saved_names, totalBytes=total_bytes)


@app.get("/documents/{document_id}/status")
async def get_status(document_id: str):
    job = JOBS.get(document_id)
    if job is None:
        raise HTTPException(404, "unknown documentId")
    # Real per-cluster progress isn't cheap to observe mid-call (run_document
    # returns once, after all clusters finish) - approximate with elapsed-time
    # easing instead of a fake linear ramp, capped below 95% until actually done.
    if not job["done"]:
        elapsed = time.time() - job.get("_started", time.time())
        job.setdefault("_started", time.time())
        progress = min(95, int(elapsed / 90 * 100))  # ~90s is a typical doc
    else:
        progress = 100
    return {
        "documentId": document_id,
        "progress": progress,
        "stage": job["stage"],
        "done": job["done"],
        "error": job["error"],
    }


# ── Field formatting: our typed schema -> the frontend's flat RfpField shape ───

_FIELD_META = {
    #        id  category
    "submission_deadline":               (1,  "deadline"),
    "questions_deadline":                (2,  "deadline"),
    "rfp_contact":                       (3,  "contact"),
    "submission_method":                 (4,  "contact"),
    "contract_term":                     (5,  "scope"),
    "scope_of_deliverables":             (6,  "scope"),
    "mandatory_submission_requirements": (7,  "requirements"),
    "mandatory_technical_requirements":  (8,  "requirements"),
    "evaluation_criteria":               (9,  "evaluation"),
    "minimum_score_threshold":           (10, "evaluation"),
    "pricing_structure":                 (11, "requirements"),
    "insurance_requirements":            (12, "compliance"),
    "vendor_experience_required":        (13, "compliance"),
    "references_required":               (14, "compliance"),
    "data_security_requirements":        (15, "compliance"),
    "data_hosting_residency":            (16, "compliance"),
    "vendor_demonstration_required":     (17, "compliance"),
}


def _format_value(key: str, answer: dict) -> Optional[str]:
    ftype = BY_KEY[key].type.value
    if ftype == "contact":
        # ContactAnswer has no top-level "value" - name/email/phone/title are
        # its own keys, unlike every other answer type.
        parts = [answer.get("name"), answer.get("email"), answer.get("phone")]
        return " — ".join(p for p in parts if p) or None
    v = answer.get("value")
    if v is None:
        return None
    if ftype == "list":
        return "; ".join(str(x) for x in v) if v else None
    if ftype == "table":
        if key == "evaluation_criteria":
            return "; ".join(
                f"{row.get('category')}: {row.get('weight')}{row.get('unit') or ''}" for row in v
            ) if v else None
        if key == "insurance_requirements":
            return "; ".join(
                f"{row.get('coverage_type')}: {row.get('amount')} {row.get('currency') or ''} "
                f"({row.get('basis') or ''})".strip()
                for row in v
            ) if v else None
    if ftype == "number":
        unit = answer.get("unit")
        return f"{v}{' ' + unit if unit else ''}"
    if ftype == "boolean":
        return "Yes" if v else "No"
    if ftype == "datetime":
        return answer.get("raw") or str(v)
    return str(v)


def _to_rfp_field(key: str, answer: Optional[dict]) -> dict:
    field_id, category = _FIELD_META[key]
    label = BY_KEY[key].label
    if not answer or not answer.get("present"):
        return {
            "id": field_id, "category": category, "status": "not_found",
            "confidence": "not_found", "label": label, "labelAr": label,
            "value": None, "valueAr": None,
        }

    conf = float(answer.get("confidence", 0.5))
    conf_bucket = "high" if conf >= 0.8 else "medium" if conf >= 0.5 else "low"
    evidence_status = answer.get("_evidence", {}).get("status")
    status = "found" if evidence_status == "verified" and conf_bucket != "low" else "needs_review"

    value_str = _format_value(key, answer)
    quote = answer.get("quote")
    page = answer.get("page")

    out = {
        "id": field_id, "category": category, "status": status,
        "confidence": conf_bucket, "confidencePct": round(conf * 100),
        "label": label, "labelAr": label,
        "value": value_str, "valueAr": value_str,
        "pageRef": f"p. {page}" if page else None,
        "source": quote, "sourceAr": quote,
    }
    if status == "needs_review":
        reason = {
            "verified": "Model confidence for this extraction was low.",
            "wrong_page": "The citation points to a different page than claimed - verify manually.",
            "unverified": "The citation could not be mechanically verified against the source text.",
            "no_quote": "The model did not provide a supporting quote for this value.",
        }.get(evidence_status, "This extraction may need manual review.")
        out["confidenceReason"] = reason
        out["confidenceReasonAr"] = reason
    return out


@app.get("/documents/{document_id}/fields")
async def get_fields(document_id: str):
    job = JOBS.get(document_id)
    if job is None:
        raise HTTPException(404, "unknown documentId")
    if not job["done"]:
        raise HTTPException(409, "extraction still in progress")
    if job["error"]:
        raise HTTPException(500, job["error"])

    fields = [_to_rfp_field(f.key, job["fields"].get(f.key)) for f in FIELDS]
    return {
        "documentId": document_id,
        "fields": fields,
        "pageCount": job["page_count"],
        "detectedLanguage": "en",
    }


# ── Agent - cross-document consistency review, runs on the same local model ────
# Different task shape from the 17-field extraction: instead of pulling specific
# known facts, this reads broadly across the whole document looking for internal
# contradictions (conflicting dates, mismatched requirement counts, references to
# missing appendices, ambiguous mandatory-vs-optional language, etc). One call,
# not six clusters - there's no natural way to split "does anything in this
# document contradict anything else" into independent page-scoped questions.

_AGENT_CATEGORIES = ["dates", "submission", "requirements", "evaluation", "contract",
                     "compliance", "references", "cross_references", "ambiguity", "other"]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SourceModel(_Strict):
    page: int = Field(description="1-based page number this evidence is on.")
    quote: str = Field(description="Verbatim text from that page.")


class FindingModel(_Strict):
    title: str = Field(description="Short, specific label, e.g. 'Conflicting Submission Deadline'.")
    severity: Literal["critical", "high", "medium", "low"]
    category: Literal[tuple(_AGENT_CATEGORIES)]
    type: Literal["confirmed", "potential"] = Field(
        description="'confirmed' = the contradiction is directly readable from the two quotes. "
                    "'potential' = worth a human double-checking, not fully certain.")
    explanation: str = Field(description="What the issue is, citing the specific conflicting facts.")
    why_it_matters: str = Field(description="Concrete consequence for a vendor reading this RFP.")
    sources: List[SourceModel] = Field(description="1-3 page+quote pairs supporting this finding.")
    confidence: float = Field(description="0.0-1.0.")


class AgentAnalysis(_Strict):
    findings: List[FindingModel]


_AGENT_SYSTEM = """You are reviewing an RFP (Request for Proposal) document for internal \
consistency issues - the kind a careful vendor or procurement reviewer would flag before \
responding. You are NOT extracting facts; you are looking for problems.

Look specifically for:
- Conflicting dates, dollar amounts, or counts stated more than once in the document
- A section referencing an appendix, exhibit, or section number that doesn't appear to exist
- Ambiguous mandatory-vs-optional language (e.g. one sentence says "shall", another says \
"should" or "may" for what looks like the same requirement)
- Evaluation criteria weights that don't sum to 100%, or a stated minimum score that \
contradicts the scoring table
- Two different instructions for how to submit, or two different contacts, for the same step
- Undefined acronyms or terms used as if already explained

Do NOT invent a problem that isn't really there. Every finding's "sources" must be an exact, \
verbatim quote from the document - fabricating a quote is worse than finding nothing. If the \
document is internally consistent on some topic, do not manufacture a finding about it just to \
have something to report. Return an empty findings list if you genuinely find nothing - that is \
a valid, common answer, not a failure."""


def _agent_schema() -> dict:
    schema = AgentAnalysis.model_json_schema()
    _inline_required(schema)
    return schema


def _run_agent_review(doc: Document) -> list[dict]:
    # Cap input to leave real headroom under the 32k context: the earlier
    # cross-cluster extraction work already established that this model can
    # burn its whole completion budget getting stuck mid-generation on a large
    # payload (see the commercial_pricing cluster note in backends.py) - same
    # risk here, amplified by a document-wide instead of page-scoped prompt.
    pages = [doc.page(n) for n in range(1, doc.n_pages + 1)]
    text = pages_as_text(pages, max_chars_per_page=3000)
    if len(text) > 100_000:
        text = text[:100_000] + "\n[... document truncated for length ...]"

    messages = [
        {"role": "system", "content": _AGENT_SYSTEM},
        {"role": "user", "content": f"Document: {doc.doc_id}\n\n{text}"},
    ]
    result = _agent_backend.call(messages, _agent_schema(), schema_name="agent_analysis")
    if not result.ok or not result.parsed:
        return []

    findings = []
    for i, raw in enumerate(result.parsed.get("findings", []), start=1):
        verified_sources = []
        any_verified = False
        for src in raw.get("sources", []):
            check = find_quote(doc, src.get("quote", ""), src.get("page"))
            verified = check["found"] and check["found_on_page"] == src.get("page")
            any_verified = any_verified or verified
            verified_sources.append({
                "page": str(src.get("page")),
                "quote": src.get("quote", ""),
                "_verified": verified,
            })
        if not any_verified:
            continue  # every cited quote failed the mechanical check - drop the finding, don't show unverifiable claims
        conf = float(raw.get("confidence", 0.5))
        findings.append({
            "id": i,
            "title": raw.get("title", ""), "titleAr": raw.get("title", ""),
            "severity": raw.get("severity", "medium"),
            "category": raw.get("category", "other"),
            "type": raw.get("type", "potential"),
            "explanation": raw.get("explanation", ""), "explanationAr": raw.get("explanation", ""),
            "whyItMatters": raw.get("why_it_matters", ""), "whyItMattersAr": raw.get("why_it_matters", ""),
            "sources": [{"page": s["page"], "quote": s["quote"], "quoteAr": s["quote"]} for s in verified_sources],
            "confidence": "high" if conf >= 0.8 else "medium" if conf >= 0.5 else "low",
            "confidencePct": round(conf * 100),
        })
    return findings


@app.post("/documents/{document_id}/review")
async def run_agent(document_id: str):
    job = JOBS.get(document_id)
    if job is None:
        raise HTTPException(404, "unknown documentId")
    doc = _get_doc(document_id)
    findings = _run_agent_review(doc)
    return {"findings": findings}


# ── Chat / RAG - stays on OpenAI throughout, per instruction ───────────────────

_openai_client: Optional[OpenAI] = None
_doc_cache: dict[str, Document] = {}


def _openai() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    return _openai_client


def _get_doc(document_id: str) -> Document:
    if document_id not in _doc_cache:
        job = JOBS.get(document_id)
        if job is None:
            raise HTTPException(404, "unknown documentId")
        _doc_cache[document_id] = Document.load(job["pdf_path"])
    return _doc_cache[document_id]


_STOPWORDS = {"what", "happens", "if", "cannot", "the", "with", "to", "a", "an",
              "of", "is", "are", "does", "for", "in", "this", "will", "and", "or"}


def _retrieve(doc: Document, question: str, top_k: int = 5) -> list:
    q_vec = _embed([question])[0]
    pages_emb = doc.page_embeddings()
    emb_scored = sorted(
        ((_cosine(q_vec, vec), doc.page(n)) for n, vec in pages_emb.items()),
        key=lambda sp: (-sp[0], sp[1].number),
    )
    keywords = [w for w in question.lower().replace("?", "").split() if w not in _STOPWORDS]
    kw_scored = _score_pages(doc, keywords)
    emb_rank = {p.number: i for i, (_, p) in enumerate(emb_scored)}
    kw_rank = {p.number: i for i, (_, p) in enumerate(kw_scored)}
    fused = []
    for n in set(emb_rank) | set(kw_rank):
        score = (1 / (60 + emb_rank[n]) if n in emb_rank else 0) + \
                (1 / (60 + kw_rank[n]) if n in kw_rank else 0)
        fused.append((score, doc.page(n)))
    fused.sort(key=lambda sp: (-sp[0], sp[1].number))
    return [p for _, p in fused[:top_k]]


class ChatTurnModel(BaseModel):
    role: str
    text: str


class ChatRequestModel(BaseModel):
    documentId: str
    message: str
    history: list[ChatTurnModel] = []
    lang: str = "en"


@app.post("/chat")
async def chat(req: ChatRequestModel):
    doc = _get_doc(req.documentId)
    pages = _retrieve(doc, req.message)
    context = "\n\n".join(f"--- PAGE {p.number} ---\n{p.text}" for p in pages)

    lang_note = " Respond in Arabic." if req.lang == "ar" else ""
    messages = [
        {"role": "system", "content":
            "Answer the question using ONLY the provided page excerpts from this RFP "
            "document. Cite the page number(s) you used. If the answer isn't in the "
            "excerpts, say clearly that it is not stated in the document - do not "
            "guess or invent an answer." + lang_note},
    ]
    for turn in req.history[-6:]:
        messages.append({"role": "user" if turn.role == "user" else "assistant", "content": turn.text})
    messages.append({"role": "user", "content": f"PAGES:\n{context}\n\nQUESTION: {req.message}"})

    resp = _openai().chat.completions.create(model="gpt-4o", messages=messages, temperature=0)
    text = resp.choices[0].message.content
    refs = [f"Page {p.number}" for p in pages[:3]]
    return {"text": text, "refs": refs}


@app.get("/health")
async def health():
    return {"ok": True}


# ── Frontend static files (built React app) ────────────────────────────────
# Mounted last so it never shadows the API routes above; falls back to
# index.html for client-side routing (html=True).
_FRONTEND_DIST = Path(os.environ.get("FRONTEND_DIST", str(Path(__file__).parent / "frontend_dist")))
if _FRONTEND_DIST.is_dir():
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=str(_FRONTEND_DIST), html=True), name="frontend")

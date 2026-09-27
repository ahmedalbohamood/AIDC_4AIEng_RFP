// ─────────────────────────────────────────────────────────────────────────────
// RFP Extract — API Integration Layer
// ─────────────────────────────────────────────────────────────────────────────
//
// Talks to server.py: extraction runs on our own local model, chat/RAG stays
// on OpenAI. Set VITE_API_BASE_URL in .env (defaults to localhost:8420).
// ─────────────────────────────────────────────────────────────────────────────

import type {
  UploadResponse,
  ExtractionJobStatus,
  ExtractionResult,
  ChatRequest,
  ChatResponse,
  AgentFinding,
} from './types'

// ── Configuration ─────────────────────────────────────────────────────────────

export const API_BASE = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8420'

/** Build standard request headers. Add Authorization here when needed. */
function buildHeaders(extra: Record<string, string> = {}): HeadersInit {
  return {
    // 'Authorization': `Bearer ${import.meta.env.VITE_API_KEY}`,
    ...extra,
  }
}

/** Throw a typed error for non-2xx responses. */
async function assertOk(res: Response): Promise<void> {
  if (!res.ok) {
    const body = await res.text().catch(() => '')
    throw new Error(`API ${res.status}: ${body || res.statusText}`)
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// 1. UPLOAD DOCUMENT
//    POST /documents
//    Accepts one or more RFP files (PDF, DOCX, TXT).
//    Returns a documentId used for all subsequent calls.
// ─────────────────────────────────────────────────────────────────────────────

export async function uploadDocument(files: File[]): Promise<UploadResponse> {
  const form = new FormData()
  files.forEach(f => form.append('files', f))

  const res = await fetch(`${API_BASE}/documents`, {
    method: 'POST',
    headers: buildHeaders(),   // do NOT add Content-Type; browser sets multipart boundary
    body: form,
  })
  await assertOk(res)
  return res.json() as Promise<UploadResponse>
}

// ─────────────────────────────────────────────────────────────────────────────
// 2. POLL EXTRACTION STATUS
//    GET /documents/:id/status
//    Call on an interval (~1 s) until `done === true`.
//    The `stage` string is shown in the processing UI.
// ─────────────────────────────────────────────────────────────────────────────

export async function getExtractionStatus(documentId: string): Promise<ExtractionJobStatus> {
  const res = await fetch(`${API_BASE}/documents/${documentId}/status`, {
    headers: buildHeaders(),
  })
  await assertOk(res)
  return res.json() as Promise<ExtractionJobStatus>
}

// ─────────────────────────────────────────────────────────────────────────────
// 3. FETCH EXTRACTED FIELDS
//    GET /documents/:id/fields
//    Returns the 17 structured RFP fields after extraction is complete.
// ─────────────────────────────────────────────────────────────────────────────

export async function getExtractedFields(documentId: string): Promise<ExtractionResult> {
  const res = await fetch(`${API_BASE}/documents/${documentId}/fields`, {
    headers: buildHeaders(),
  })
  await assertOk(res)
  return res.json() as Promise<ExtractionResult>
}

// ─────────────────────────────────────────────────────────────────────────────
// 4. SEND CHAT MESSAGE
//    POST /chat
//    Accepts the user message + conversation history.
//    Returns the assistant reply and optional source references.
// ─────────────────────────────────────────────────────────────────────────────

export async function sendChatMessage(req: ChatRequest): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: buildHeaders({ 'Content-Type': 'application/json' }),
    body: JSON.stringify(req),
  })
  await assertOk(res)
  return res.json() as Promise<ChatResponse>
}

// (No 5th endpoint: validateField was unused by the UI and only ever had a mock
// implementation - removed rather than wired up, per "delete the unnecessary
// things." Re-add it here + as a server.py route if per-field re-validation is
// ever built.)

// ─────────────────────────────────────────────────────────────────────────────
// 6. RUN AGENT REVIEW
//    POST /documents/:id/review
//    Scans the whole document for internal contradictions/ambiguities.
// ─────────────────────────────────────────────────────────────────────────────

export async function runAgentReview(documentId: string): Promise<AgentFinding[]> {
  const res = await fetch(`${API_BASE}/documents/${documentId}/review`, {
    method: 'POST',
    headers: buildHeaders(),
  })
  await assertOk(res)
  const data = await res.json() as { findings: AgentFinding[] }
  return data.findings
}

// ─────────────────────────────────────────────────────────────────────────────
// RFP Extract — Shared Types
// ─────────────────────────────────────────────────────────────────────────────

export type Lang       = 'en' | 'ar'
export type ThemeMode  = 'light' | 'dark' | 'system'
export type AppView    = 'extraction' | 'chat' | 'agent'
export type Category   = 'deadline' | 'contact' | 'scope' | 'requirements' | 'evaluation' | 'compliance'
export type FieldStatus   = 'found' | 'not_found' | 'needs_review'
export type Confidence    = 'high' | 'medium' | 'low' | 'not_found'
export type StatusFilter  = 'all' | 'found' | 'not_found' | 'needs_review'
export type ConfFilter    = 'all' | 'high' | 'medium' | 'low'

// ── Extracted RFP field ───────────────────────────────────────────────────────

export interface RfpField {
  /** Stable numeric ID matching the 17 standard RFP field definitions */
  id: number

  /** Field display label (English) */
  label: string
  /** Field display label (Arabic) */
  labelAr: string

  /** Extraction category used for sidebar navigation */
  category: Category

  /** Extracted text value (null when not found) */
  value: string | null
  /** Arabic equivalent of the extracted value */
  valueAr: string | null

  /** Extraction confidence bucket */
  confidence: Confidence
  /** Optional 0–100 confidence score from the AI model */
  confidencePct?: number
  /** Human-readable explanation of why confidence may be lower (English) */
  confidenceReason?: string
  /** Arabic explanation */
  confidenceReasonAr?: string

  /** Read-only status derived from extraction result */
  status: FieldStatus

  /** Verbatim supporting quote from the source document (English) */
  source?: string
  /** Arabic version of the source quote */
  sourceAr?: string

  /** Page reference string, e.g. "p. 4" or "p. 7–9" */
  pageRef?: string

  /** Document section the evidence was found in (English) */
  sectionName?: string
  /** Arabic section name */
  sectionNameAr?: string
}

// ── API contract types ────────────────────────────────────────────────────────

/** POST /documents — upload one or more files */
export interface UploadResponse {
  /** Unique document / job identifier returned by the server */
  documentId: string
  /** Friendly file name(s) for display */
  fileNames: string[]
  /** Total bytes across all uploaded files */
  totalBytes: number
}

/** GET /documents/:id/status */
export interface ExtractionJobStatus {
  documentId: string
  /** 0–100; when 100 the job is complete */
  progress: number
  /** Current processing stage label (server-supplied, already localised or English) */
  stage: string
  done: boolean
  error?: string
}

/** GET /documents/:id/fields */
export interface ExtractionResult {
  documentId: string
  fields: RfpField[]
  /** Total pages analysed */
  pageCount: number
  /** ISO 639-1 language code detected, e.g. "en" or "ar" */
  detectedLanguage: string
}

/** POST /chat */
export interface ChatRequest {
  documentId: string
  message: string
  /** Conversation history for multi-turn context */
  history: ChatTurn[]
  /** Preferred response language */
  lang: Lang
}

export interface ChatTurn {
  role: 'user' | 'assistant'
  text: string
}

export interface ChatResponse {
  text: string
  /** Source references cited by the AI, if any */
  refs?: string[]
}

// ── Agent types ───────────────────────────────────────────────────────────────

export type AgentSeverity = 'critical' | 'high' | 'medium' | 'low'
export type AgentCategory =
  | 'dates' | 'submission' | 'requirements' | 'evaluation'
  | 'contract' | 'compliance' | 'references' | 'cross_references'
  | 'ambiguity' | 'other'
export type FindingType = 'confirmed' | 'potential'
export type SeverityFilter = 'all' | AgentSeverity
export type AgentCatFilter = 'all' | AgentCategory

export interface EvidenceSource {
  page: string
  section?: string
  sectionAr?: string
  quote: string
  quoteAr?: string
}

export interface AgentFinding {
  id: number
  title: string
  titleAr: string
  severity: AgentSeverity
  category: AgentCategory
  type: FindingType
  explanation: string
  explanationAr: string
  whyItMatters: string
  whyItMattersAr: string
  sources: EvidenceSource[]
  confidence: Confidence
  confidencePct?: number
}

// ── UI-only types (not sent to the API) ──────────────────────────────────────

export interface ChatMessage extends ChatTurn {
  id: number
  refs?: string[]
}

export interface UploadedFile {
  name: string
  size: number
}

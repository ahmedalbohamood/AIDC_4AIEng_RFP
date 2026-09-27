// ─────────────────────────────────────────────────────────────────────────────
// RFP Extract — Main Application
//
// Extraction, Chat, and Agent are all live against server.py: extraction runs
// on our own local model, chat/RAG stays on OpenAI, and the agent review runs
// on the same local model reading the whole document in one pass.
// ─────────────────────────────────────────────────────────────────────────────

import {
  useState, useRef, useCallback, useEffect,
  useLayoutEffect, type JSX,
} from 'react'

import {
  uploadDocument,
  getExtractionStatus,
  getExtractedFields,
  sendChatMessage,
  runAgentReview,
} from './api'

import { t as tr } from './i18n'
import { CATEGORY_ORDER } from './constants'

import type {
  Lang, ThemeMode, AppView, Category,
  FieldStatus, Confidence,
  StatusFilter, ConfFilter,
  SeverityFilter, AgentCatFilter,
  RfpField, UploadedFile, ChatMessage,
  ExtractionResult, AgentFinding,
} from './types'

// ── Theme ─────────────────────────────────────────────────────────────────────

function resolveTheme(mode: ThemeMode): boolean {
  if (mode === 'dark')  return true
  if (mode === 'light') return false
  return window.matchMedia('(prefers-color-scheme: dark)').matches
}

function tk(dark: boolean) {
  return {
    pageBg:      dark ? '#0D1117' : '#F3F6FB',
    sidebarBg:   dark ? '#0B0F1A' : '#EEF2F7',
    panelBg:     dark ? '#111827' : '#FFFFFF',
    headerBg:    dark ? '#0B0F1A' : '#FFFFFF',
    tableHead:   dark ? '#0D1220' : '#F4F7FB',
    rowEven:     dark ? '#111827' : '#FFFFFF',
    rowOdd:      dark ? '#0E1520' : '#F8FAFD',
    rowHover:    dark ? '#182540' : '#EBF3FF',
    inputBg:     dark ? '#0D1220' : '#FFFFFF',
    chipBg:      dark ? '#111827' : '#FFFFFF',
    tagBg:       dark ? '#1A2540' : '#EEF2F7',
    evidenceBg:  dark ? '#090E1A' : '#F0F5FF',
    chatUserBg:  dark ? '#1B3A6B' : '#EBF3FF',
    chatAIBg:    dark ? '#111827' : '#FFFFFF',
    border:      dark ? '#1C2D45' : '#DDE3EE',
    text:        dark ? '#E2E8F5' : '#1A2033',
    textSub:     dark ? '#7A8FB0' : '#5A6478',
    textFaint:   dark ? '#2E4060' : '#C5D0E0',
    accent:      '#2563EB',
  }
}

// ── Status & confidence config ────────────────────────────────────────────────

const STATUS_CFG: Record<FieldStatus, {
  dot: string; textL: string; textD: string; bgL: string; bgD: string; bdL: string; bdD: string
}> = {
  found:        { dot:'bg-emerald-500', textL:'text-emerald-700', textD:'text-emerald-400', bgL:'bg-emerald-50',  bgD:'bg-emerald-900/20', bdL:'border-emerald-200', bdD:'border-emerald-800' },
  needs_review: { dot:'bg-amber-500',   textL:'text-amber-700',   textD:'text-amber-400',   bgL:'bg-amber-50',    bgD:'bg-amber-900/20',   bdL:'border-amber-200',   bdD:'border-amber-800' },
  not_found:    { dot:'bg-red-500',     textL:'text-red-700',     textD:'text-red-400',     bgL:'bg-red-50',      bgD:'bg-red-900/20',     bdL:'border-red-200',     bdD:'border-red-800' },
}

const CONF_CFG: Record<Confidence, { dot: string; textL: string; textD: string }> = {
  high:      { dot:'bg-blue-500',  textL:'text-blue-700',  textD:'text-blue-400' },
  medium:    { dot:'bg-amber-500', textL:'text-amber-700', textD:'text-amber-400' },
  low:       { dot:'bg-red-500',   textL:'text-red-600',   textD:'text-red-400' },
  not_found: { dot:'bg-gray-400',  textL:'text-gray-500',  textD:'text-gray-400' },
}

// ── Tiny icon set ─────────────────────────────────────────────────────────────

const Icon: Record<string, (p?: Record<string, unknown>) => JSX.Element> = {
  Sun:      () => <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><circle cx="7" cy="7" r="2.8" stroke="currentColor" strokeWidth="1.4"/><path d="M7 1v1.5M7 11.5V13M1 7h1.5M11.5 7H13M2.93 2.93l1.06 1.06M10.01 10.01l1.06 1.06M11.07 2.93l-1.06 1.06M3.99 10.01l-1.06 1.06" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/></svg>,
  Moon:     () => <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><path d="M12 9.5A6 6 0 014.5 2a6 6 0 100 10 6 6 0 007.5-2.5z" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round"/></svg>,
  Monitor:  () => <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><rect x="1" y="1.5" width="12" height="8" rx="1.5" stroke="currentColor" strokeWidth="1.3"/><path d="M5 12h4M7 9.5V12" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/></svg>,
  Search:   () => <svg width="13" height="13" viewBox="0 0 13 13" fill="none"><circle cx="5.5" cy="5.5" r="4" stroke="currentColor" strokeWidth="1.3"/><path d="M8.5 8.5l2.5 2.5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/></svg>,
  Upload:   () => <svg width="20" height="20" viewBox="0 0 20 20" fill="none"><path d="M10 3v11M5.5 7.5L10 3l4.5 4.5" stroke="#2563EB" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/><path d="M3 16h14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/></svg>,
  File:     () => <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M2 1.5h5l3 3V11a.5.5 0 01-.5.5H2a.5.5 0 01-.5-.5V2A.5.5 0 012 1.5z" stroke="currentColor" strokeWidth="1.2" fill="none"/><path d="M7 1.5V4.5h3" stroke="currentColor" strokeWidth="1.2"/></svg>,
  Chevron:  ({ open }: { open?: boolean } = {}) => <svg width="11" height="11" viewBox="0 0 11 11" fill="none" className={`transition-transform duration-150 ${open ? 'rotate-180' : ''}`}><path d="M2 3.5l3.5 3.5 3.5-3.5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/></svg>,
  Send:     () => <svg width="15" height="15" viewBox="0 0 15 15" fill="none"><path d="M13 7.5L2 2l2.5 5.5L2 13l11-5.5z" stroke="currentColor" strokeWidth="1.4" strokeLinejoin="round"/></svg>,
  Sparkle:  () => <svg width="12" height="12" viewBox="0 0 12 12" fill="white"><path d="M6 1l1.1 3.4 3.4 1.1-3.4 1.1L6 10l-1.1-3.4L1.5 5.5l3.4-1.1L6 1z" stroke="white" strokeWidth="0.8" strokeLinejoin="round"/></svg>,
  Table:    () => <svg width="13" height="13" viewBox="0 0 13 13" fill="none"><rect x="1" y="1" width="11" height="11" rx="1.5" stroke="currentColor" strokeWidth="1.2"/><path d="M1 4.5h11M4.5 4.5v7" stroke="currentColor" strokeWidth="1.2"/></svg>,
  Chat:     () => <svg width="13" height="13" viewBox="0 0 13 13" fill="none"><path d="M11.5 1.5h-10a1 1 0 00-1 1v7a1 1 0 001 1H4l2.5 2 2.5-2h2.5a1 1 0 001-1v-7a1 1 0 00-1-1z" stroke="currentColor" strokeWidth="1.2"/></svg>,
  PageRef:  () => <svg width="10" height="10" viewBox="0 0 10 10" fill="none"><rect x=".5" y=".5" width="9" height="9" rx="1" stroke="currentColor" strokeWidth="1"/><path d="M2.5 3.5h5M2.5 5.5h3" stroke="currentColor" strokeWidth="1" strokeLinecap="round"/></svg>,
  NotFound: () => <svg width="13" height="13" viewBox="0 0 13 13" fill="none"><circle cx="6.5" cy="6.5" r="5" stroke="currentColor" strokeWidth="1.3"/><path d="M4.5 4.5l4 4M8.5 4.5l-4 4" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/></svg>,
  Close:    () => <svg width="11" height="11" viewBox="0 0 11 11" fill="none"><path d="M2 2l7 7M9 2l-7 7" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round"/></svg>,
  Agent:    () => <svg width="13" height="13" viewBox="0 0 13 13" fill="none"><circle cx="6.5" cy="5.5" r="3" stroke="currentColor" strokeWidth="1.2"/><path d="M1.5 11.5c0-2.76 2.24-5 5-5s5 2.24 5 5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/><path d="M6.5 1.5v1M6.5 9v1M9.5 5.5h1M2.5 5.5h1" stroke="currentColor" strokeWidth="1.1" strokeLinecap="round"/></svg>,
  Warning:  () => <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M6 1.5L11 10H1L6 1.5z" stroke="currentColor" strokeWidth="1.2" strokeLinejoin="round"/><path d="M6 5v2.5M6 8.5v.5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/></svg>,
  Flag:     () => <svg width="12" height="12" viewBox="0 0 12 12" fill="none"><path d="M2 2h8l-2 3 2 3H2" stroke="currentColor" strokeWidth="1.2" strokeLinejoin="round"/><path d="M2 2v9" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/></svg>,
  AskAI:    () => <svg width="10" height="10" viewBox="0 0 10 10" fill="none"><path d="M5 1l.85 2.65L8.5 4.5l-2.65.85L5 8l-.85-2.65L1.5 4.5l2.65-.85L5 1z" stroke="currentColor" strokeWidth="1.1" strokeLinejoin="round"/></svg>,
  Check:    () => <svg width="11" height="11" viewBox="0 0 11 11" fill="none"><path d="M2 5.5l2.5 2.5L9 3" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/></svg>,
  Info:     () => <svg width="11" height="11" viewBox="0 0 11 11" fill="none"><circle cx="5.5" cy="5.5" r="4.5" stroke="currentColor" strokeWidth="1.1"/><path d="M5.5 4v4M5.5 3v-.5" stroke="currentColor" strokeWidth="1.1" strokeLinecap="round"/></svg>,
  Globe:    () => <svg width="13" height="13" viewBox="0 0 13 13" fill="none"><circle cx="6.5" cy="6.5" r="5" stroke="currentColor" strokeWidth="1.2"/><path d="M6.5 1.5c-2 1.5-2 8.5 0 10M6.5 1.5c2 1.5 2 8.5 0 10M1.5 6.5h10" stroke="currentColor" strokeWidth="1.2"/></svg>,
}

function fmt(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1048576).toFixed(1)} MB`
}

// ─────────────────────────────────────────────────────────────────────────────
// COMPONENTS
// ─────────────────────────────────────────────────────────────────────────────

// ── Confidence badge ──────────────────────────────────────────────────────────

function ConfBadge({ c, pct, reason, dark, lang }: {
  c: Confidence; pct?: number; reason?: string; dark: boolean; lang: Lang
}) {
  const [tip, setTip] = useState(false)
  const t = tk(dark)
  const cfg = CONF_CFG[c]
  const strings = tr(lang)
  const label = { high: strings.high, medium: strings.medium, low: strings.low, not_found: strings.na }[c]

  return (
    <div className="relative inline-flex items-center gap-1.5">
      <span className={`inline-flex items-center gap-1.5 text-[11px] font-500 ${dark ? cfg.textD : cfg.textL}`}>
        <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${cfg.dot}`} />
        {label}{pct !== undefined ? ` · ${pct}%` : ''}
      </span>
      {reason && (
        <button onMouseEnter={() => setTip(true)} onMouseLeave={() => setTip(false)}
          className="opacity-40 hover:opacity-100 transition-opacity" style={{ color: t.textSub }}>
          <Icon.Info />
        </button>
      )}
      {tip && reason && (
        <div className="absolute bottom-full left-0 mb-2 z-30 w-56 rounded-[6px] p-2.5 text-[11px] leading-snug shadow-lg"
          style={{ background: dark ? '#1A2540' : '#20242B', color: '#E2E8F5', border: `1px solid ${t.border}` }}>
          <div className="font-600 mb-1" style={{ color: '#93B4F0' }}>{strings.confTooltipTitle}</div>
          {reason}
        </div>
      )}
    </div>
  )
}

function StatusBadge({ s, dark, lang }: { s: FieldStatus; dark: boolean; lang: Lang }) {
  const cfg = STATUS_CFG[s]
  const strings = tr(lang)
  const label = { found: strings.found, not_found: strings.notFound, needs_review: strings.needsReview }[s]
  return (
    <span className={`text-[10px] font-500 border rounded-[4px] px-1.5 py-0.5 ${dark ? `${cfg.textD} ${cfg.bgD} ${cfg.bdD}` : `${cfg.textL} ${cfg.bgL} ${cfg.bdL}`}`}>
      {label}
    </span>
  )
}

// ── Sidebar ───────────────────────────────────────────────────────────────────

function Sidebar({ view, onView, catFilter, onCat, statusFilter, onStatus, dark, lang, fields }: {
  view: AppView; onView: (v: AppView) => void
  catFilter: Category | 'all'; onCat: (c: Category | 'all') => void
  statusFilter: StatusFilter; onStatus: (s: StatusFilter) => void
  dark: boolean; lang: Lang; fields: RfpField[]
}) {
  const t = tk(dark)
  const strings = tr(lang)
  const isRtl = lang === 'ar'
  const font = isRtl ? 'Cairo, sans-serif' : 'Inter, sans-serif'

  const counts = fields.reduce((a, f) => { a[f.category] = (a[f.category] || 0) + 1; return a }, {} as Record<string,number>)
  const found   = fields.filter(f => f.status === 'found').length
  const missing = fields.filter(f => f.status === 'not_found').length
  const review  = fields.filter(f => f.status === 'needs_review').length

  function NavBtn({ active, label, count, onClick }: {
    active: boolean; label: string; count?: number; onClick: () => void
  }) {
    const [hover, setHover] = useState(false)
    return (
      <div onClick={onClick} onMouseEnter={() => setHover(true)} onMouseLeave={() => setHover(false)}
        className={`flex items-center justify-between px-2.5 py-1.5 rounded-[6px] cursor-pointer select-none text-[12.5px] font-500 transition-colors ${isRtl ? 'flex-row-reverse' : ''}`}
        style={{ background: active ? '#2563EB' : hover ? (dark ? '#1A2842' : '#DCE5F0') : 'transparent', color: active ? '#fff' : t.text }}>
        <span>{label}</span>
        {count !== undefined && <span style={{ color: active ? 'rgba(255,255,255,.6)' : t.textSub, fontSize: 11 }} className="tabular-nums">{count}</span>}
      </div>
    )
  }

  return (
    <aside className="w-[214px] shrink-0 flex flex-col h-full transition-colors duration-200"
      style={{ background: t.sidebarBg, fontFamily: font, [isRtl ? 'borderLeft' : 'borderRight']: `1px solid ${t.border}` }}>

      {/* Logo */}
      <div className={`px-4 py-4 shrink-0 flex items-center gap-2.5 ${isRtl ? 'flex-row-reverse' : ''}`}
        style={{ borderBottom: `1px solid ${t.border}` }}>
        <div className="w-7 h-7 rounded-[6px] bg-[#2563EB] flex items-center justify-center shrink-0">
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <rect x="1" y="1" width="5" height="5" rx="1" fill="white"/>
            <rect x="8" y="1" width="5" height="5" rx="1" fill="white" fillOpacity=".5"/>
            <rect x="1" y="8" width="5" height="5" rx="1" fill="white" fillOpacity=".5"/>
            <rect x="8" y="8" width="5" height="5" rx="1" fill="white"/>
          </svg>
        </div>
        <div className={isRtl ? 'text-right' : ''}>
          <div className="text-[13px] font-700 leading-tight" style={{ color: t.text }}>{strings.brand}</div>
          <div className="text-[10px]" style={{ color: t.textSub }}>{strings.tagline}</div>
        </div>
      </div>

      {/* View switcher — 3 tabs */}
      <div className="px-3 pt-3 pb-2 shrink-0">
        <div className="flex rounded-[6px] p-0.5" style={{ background: t.border }}>
          {([
            ['extraction', <Icon.Table />, strings.extract],
            ['chat',       <Icon.Chat />,  strings.chat],
            ['agent',      <Icon.Agent />, strings.agent],
          ] as [AppView, JSX.Element, string][]).map(([v, icon, label]) => (
            <button key={v} onClick={() => onView(v)}
              className="flex-1 flex items-center justify-center gap-1 py-1.5 rounded-[5px] text-[10.5px] font-500 transition-colors"
              style={{ background: view === v ? t.panelBg : 'transparent', color: view === v ? t.text : t.textSub }}>
              {icon}{label}
            </button>
          ))}
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-2 space-y-4">
        <div>
          <div className={`text-[10px] font-600 uppercase tracking-widest px-1 mb-1.5 ${isRtl ? 'text-right' : ''}`} style={{ color: t.textSub }}>{strings.categories}</div>
          <NavBtn active={catFilter==='all'} label={strings.allFields} count={fields.length} onClick={() => onCat('all')} />
          {CATEGORY_ORDER.map(cat => (
            <NavBtn key={cat} active={catFilter===cat} label={(strings.catLabels as Record<string,string>)[cat]} count={counts[cat]||0} onClick={() => onCat(cat)} />
          ))}
        </div>

        <div>
          <div className={`text-[10px] font-600 uppercase tracking-widest px-1 mb-1.5 ${isRtl ? 'text-right' : ''}`} style={{ color: t.textSub }}>{strings.status}</div>
          <NavBtn active={statusFilter==='all'}          label={strings.allStatus}   onClick={() => onStatus('all')} />
          <NavBtn active={statusFilter==='found'}        label={strings.found}       count={found}   onClick={() => onStatus('found')} />
          <NavBtn active={statusFilter==='needs_review'} label={strings.needsReview} count={review}  onClick={() => onStatus('needs_review')} />
          <NavBtn active={statusFilter==='not_found'}    label={strings.notFound}    count={missing} onClick={() => onStatus('not_found')} />
        </div>

        <div>
          <div className={`text-[10px] font-600 uppercase tracking-widest px-1 mb-1.5 ${isRtl ? 'text-right' : ''}`} style={{ color: t.textSub }}>{strings.recent}</div>
          {strings.recentDocs.map((name, i) => (
            <div key={i} className={`flex items-center gap-2 px-2.5 py-1.5 rounded-[6px] cursor-pointer text-[12px] truncate ${isRtl ? 'flex-row-reverse' : ''}`}
              style={{ color: t.textSub }}>
              <span style={{ color: t.textFaint }}><Icon.File /></span>
              <span className="truncate">{name}</span>
            </div>
          ))}
        </div>
      </nav>

      <div className="px-4 py-3 shrink-0 text-[11px]" style={{ borderTop: `1px solid ${t.border}`, color: t.textSub, fontFamily: 'Inter, sans-serif' }}>
        {strings.version}
      </div>
    </aside>
  )
}

// ── KPI row ───────────────────────────────────────────────────────────────────

function KpiRow({ dark, lang, fields, pageCount }: {
  dark: boolean; lang: Lang; fields: RfpField[]; pageCount: number
}) {
  const t = tk(dark)
  const strings = tr(lang)
  const isRtl = lang === 'ar'
  const found    = fields.filter(f => f.status === 'found').length
  const missing  = fields.filter(f => f.status === 'not_found').length
  const review   = fields.filter(f => f.status === 'needs_review').length
  const highConf = fields.filter(f => f.confidence === 'high').length
  const confPct  = fields.length > 0 ? Math.round((highConf / fields.length) * 100) : 0

  const tiles = [
    { label: strings.fieldsFound,    value: found,         sub: `${fields.length} ${strings.ofTotal}`,      color: '#10B981' },
    { label: strings.missingFields,  value: missing,       sub: strings.fromDoc,                             color: '#EF4444' },
    { label: strings.needsReviewKpi, value: review,        sub: strings.manualCheck,                         color: '#F59E0B' },
    { label: strings.avgConf,        value: `${confPct}%`, sub: `${highConf} ${strings.highConfFields}`,     color: '#2563EB' },
    { label: strings.pagesProcessed, value: pageCount,     sub: strings.fromUpload,                          color: '#8B5CF6' },
    { label: strings.coverage,       value: strings.coverageVal, sub: `${strings.docLang} · ${strings.docTypeVal}`, color: '#0891B2' },
  ]

  return (
    <div className="grid gap-3" style={{ gridTemplateColumns: 'repeat(6, 1fr)' }}>
      {tiles.map(tile => (
        <div key={tile.label} className="rounded-[8px] px-3.5 py-3 transition-colors"
          style={{ background: t.panelBg, border: `1px solid ${t.border}`, textAlign: isRtl ? 'right' : 'left' }}>
          <div className="text-[9.5px] font-600 uppercase tracking-wider mb-1" style={{ color: t.textSub }}>{tile.label}</div>
          <div className="text-[22px] font-700 tabular-nums leading-tight" style={{ color: tile.color }}>{tile.value}</div>
          <div className="text-[10px] mt-0.5 leading-snug" style={{ color: t.textFaint }}>{tile.sub}</div>
        </div>
      ))}
    </div>
  )
}

// ── Upload zone ───────────────────────────────────────────────────────────────

function UploadZone({ onUpload, dark, lang }: {
  onUpload: (files: File[]) => void; dark: boolean; lang: Lang
}) {
  const [dragging, setDragging] = useState(false)
  const ref = useRef<HTMLInputElement>(null)
  const t = tk(dark)
  const strings = tr(lang)
  const isRtl = lang === 'ar'

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault(); setDragging(false)
    if (e.dataTransfer.files.length) onUpload(Array.from(e.dataTransfer.files))
  }, [onUpload])

  return (
    <div onDragOver={e => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)} onDrop={onDrop}
      onClick={() => ref.current?.click()}
      className="rounded-[10px] border-2 border-dashed cursor-pointer flex flex-col items-center justify-center gap-4 py-16 transition-all"
      style={{ background: dragging ? (dark ? '#1A2842' : '#EBF5FF') : t.panelBg, borderColor: dragging ? '#2563EB' : t.border, direction: isRtl ? 'rtl' : 'ltr' }}>
      <input ref={ref} type="file" multiple accept=".pdf,.doc,.docx,.txt" className="hidden"
        onChange={e => e.target.files && onUpload(Array.from(e.target.files))} />
      <div className="w-14 h-14 rounded-[10px] flex items-center justify-center"
        style={{ background: dark ? '#172035' : '#EEF5FF', border: `1px solid ${t.border}` }}>
        <Icon.Upload />
      </div>
      <div className="text-center space-y-1.5">
        <p className="text-[15px] font-600" style={{ color: t.text }}>{dragging ? strings.dragging : strings.uploadTitle}</p>
        <p className="text-[12.5px]" style={{ color: t.textSub }}>{strings.uploadSub}</p>
        <p className="text-[11.5px]" style={{ color: t.textSub }}>{strings.uploadHint}</p>
      </div>
      <div className="flex gap-2">
        {['PDF','DOCX','TXT'].map(ext => (
          <span key={ext} className="text-[11px] font-500 rounded-[5px] px-2.5 py-1"
            style={{ color: t.textSub, background: t.tagBg, border: `1px solid ${t.border}` }}>{ext}</span>
        ))}
      </div>
    </div>
  )
}

// ── Processing ────────────────────────────────────────────────────────────────

function Processing({ files, progress, dark, lang }: {
  files: UploadedFile[]; progress: number; dark: boolean; lang: Lang
}) {
  const t = tk(dark)
  const strings = tr(lang)
  const steps = strings.processingSteps
  const activeStep = Math.min(Math.floor((progress / 100) * (steps.length - 1)), steps.length - 1)

  return (
    <div className="rounded-[10px] p-6 space-y-5" style={{ background: t.panelBg, border: `1px solid ${t.border}` }}>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-2 h-2 rounded-full bg-[#2563EB] animate-pulse" />
          <span className="text-[13px] font-600" style={{ color: t.text }}>
            {progress >= 100 ? strings.processDone : strings.aiExtract}
          </span>
        </div>
        <span className="text-[13px] tabular-nums font-700" style={{ color: '#2563EB' }}>{progress}%</span>
      </div>
      <div className="h-1.5 rounded-full overflow-hidden" style={{ background: t.tagBg }}>
        <div className="h-full rounded-full bg-[#2563EB] transition-all duration-300" style={{ width: `${progress}%` }} />
      </div>
      <div className="space-y-2">
        {steps.map((step, i) => {
          const done   = i < activeStep || progress >= 100
          const active = i === activeStep && progress < 100
          return (
            <div key={i} className="flex items-center gap-3">
              <div className="w-5 h-5 rounded-full flex items-center justify-center shrink-0 transition-all"
                style={{ background: done ? '#2563EB' : active ? 'rgba(37,99,235,.15)' : t.tagBg, border: active ? '2px solid #2563EB' : 'none' }}>
                {done   && <span className="text-white"><Icon.Check /></span>}
                {active && <div className="w-1.5 h-1.5 rounded-full bg-[#2563EB] animate-pulse" />}
              </div>
              <span className="text-[12px]" style={{ color: done || active ? t.text : t.textSub, fontWeight: active ? 600 : 400 }}>{step}</span>
            </div>
          )
        })}
      </div>
      {files.map((f, i) => (
        <div key={i} className="flex items-center gap-2 text-[11.5px]" style={{ color: t.textSub }}>
          <span style={{ color: '#2563EB' }}><Icon.File /></span>
          {f.name} · {fmt(f.size)}
        </div>
      ))}
    </div>
  )
}

// ── Evidence panel ────────────────────────────────────────────────────────────

function EvidencePanel({ field, dark, lang, onClose, onAskAI }: {
  field: RfpField; dark: boolean; lang: Lang; onClose: () => void; onAskAI: (q: string) => void
}) {
  const t = tk(dark)
  const strings = tr(lang)
  const isRtl = lang === 'ar'
  const label   = isRtl ? field.labelAr   : field.label
  const source  = isRtl ? (field.sourceAr || field.source)           : field.source
  const section = isRtl ? (field.sectionNameAr || field.sectionName) : field.sectionName
  const reason  = isRtl ? field.confidenceReasonAr : field.confidenceReason

  return (
    <div className="rounded-[8px] p-4 space-y-3" style={{ background: t.evidenceBg, border: `1px solid ${dark ? '#1A3060' : '#C5D8F8'}`, direction: isRtl ? 'rtl' : 'ltr' }}>
      <div className={`flex items-start justify-between gap-2 ${isRtl ? 'flex-row-reverse' : ''}`}>
        <div>
          <div className="text-[10px] font-600 uppercase tracking-widest mb-1" style={{ color: t.textSub }}>{strings.sourceExcerpt}</div>
          <div className="text-[12px] font-600" style={{ color: t.text }}>{label}</div>
          {field.pageRef && (
            <div className={`flex items-center gap-1.5 mt-1 text-[11px] ${isRtl ? 'flex-row-reverse' : ''}`} style={{ color: '#2563EB' }}>
              <Icon.PageRef />
              {strings.page} {field.pageRef.replace('p. ','')}
              {section ? ` · ${section}` : ''}
            </div>
          )}
        </div>
        <button onClick={onClose} className="opacity-40 hover:opacity-100 transition-opacity shrink-0" style={{ color: t.text }}><Icon.Close /></button>
      </div>

      {source
        ? <blockquote className="text-[12px] italic leading-relaxed py-0.5"
            style={{ [isRtl ? 'borderRight' : 'borderLeft']: '2px solid #2563EB', [isRtl ? 'paddingRight' : 'paddingLeft']: 12, color: t.textSub }}>
            {source}
          </blockquote>
        : <div className={`flex items-center gap-2 text-[12px] ${isRtl ? 'flex-row-reverse' : ''}`} style={{ color: t.textSub }}>
            <Icon.NotFound />{strings.notFoundDoc}
          </div>
      }

      <div className={`flex items-center gap-3 ${isRtl ? 'flex-row-reverse' : ''}`}>
        <ConfBadge c={field.confidence} pct={field.confidencePct} reason={reason} dark={dark} lang={lang} />
        <StatusBadge s={field.status} dark={dark} lang={lang} />
      </div>

      <button onClick={() => onAskAI(lang === 'ar'
          ? `أخبرني المزيد عن "${field.labelAr}"`
          : `Tell me more about "${field.label}"`)}
        className={`flex items-center gap-1.5 text-[11px] font-500 px-2.5 py-1.5 rounded-[5px] transition-colors ${isRtl ? 'flex-row-reverse' : ''}`}
        style={{ background: dark ? '#172035' : '#EEF5FF', color: '#2563EB', border: `1px solid ${dark ? '#1E3A6A' : '#BFDBFE'}` }}>
        <Icon.AskAI /> {strings.askAIAbout}
      </button>
    </div>
  )
}

// ── Evaluation Insights ───────────────────────────────────────────────────────

function EvalInsights({ dark, lang, fields }: { dark: boolean; lang: Lang; fields: RfpField[] }) {
  const t = tk(dark)
  const strings = tr(lang)
  const isRtl = lang === 'ar'
  const missing  = fields.filter(f => f.status === 'not_found')
  const lowConf  = fields.filter(f => f.confidence === 'medium' || f.confidence === 'low')
  const deadlines = fields.filter(f => f.category === 'deadline' && f.value)
  const mandatory = fields.filter(f => f.category === 'requirements' && f.status === 'found').slice(0, 2)

  return (
    <div className="rounded-[10px] overflow-hidden" style={{ border: `1px solid ${t.border}` }}>
      <div className={`flex items-center gap-2 px-4 py-3 ${isRtl ? 'flex-row-reverse' : ''}`}
        style={{ background: t.tableHead, borderBottom: `1px solid ${t.border}` }}>
        <div className="w-5 h-5 rounded-[5px] bg-[#2563EB] flex items-center justify-center shrink-0"><Icon.Sparkle /></div>
        <span className="text-[13px] font-600" style={{ color: t.text }}>{strings.evalInsights}</span>
      </div>
      <div className="grid grid-cols-2" style={{ background: t.panelBg }}>
        {[
          { title: strings.missingInfo,        color: '#EF4444', items: missing.map(f => isRtl ? f.labelAr : f.label) },
          { title: strings.lowConf,            color: '#F59E0B', items: lowConf.map(f => `${isRtl?f.labelAr:f.label}${f.confidencePct?` (${f.confidencePct}%)`:''}`) },
          { title: strings.upcomingDeadlines,  color: '#2563EB', items: deadlines.map(f => `${isRtl?f.labelAr:f.label}: ${isRtl?f.valueAr:f.value}`) },
          { title: strings.mandatoryItems,     color: '#10B981', items: mandatory.map(f => isRtl ? f.labelAr : f.label) },
        ].map((section, i) => (
          <div key={i} className="p-4"
            style={{ borderRight: i%2===0 ? `1px solid ${t.border}` : 'none', borderBottom: i<2 ? `1px solid ${t.border}` : 'none', textAlign: isRtl?'right':'left' }}>
            <div className="text-[10px] font-600 uppercase tracking-widest mb-2" style={{ color: section.color }}>{section.title}</div>
            {section.items.length === 0
              ? <div className="text-[11px]" style={{ color: t.textFaint }}>—</div>
              : section.items.map((item, j) => (
                <div key={j} className={`flex items-start gap-1.5 text-[11.5px] mb-1 ${isRtl?'flex-row-reverse':''}`} style={{ color: t.textSub }}>
                  <span className="w-1 h-1 rounded-full mt-1.5 shrink-0" style={{ background: section.color }} />
                  <span className="leading-snug">{item}</span>
                </div>
              ))
            }
          </div>
        ))}
      </div>
    </div>
  )
}

// ── Extraction table ──────────────────────────────────────────────────────────

function ExtractionTable({ fields, dark, lang, onAskAI }: {
  fields: RfpField[]; dark: boolean; lang: Lang; onAskAI: (q: string) => void
}) {
  const t = tk(dark)
  const strings = tr(lang)
  const isRtl = lang === 'ar'
  const [expanded, setExpanded] = useState<number | null>(null)

  if (fields.length === 0) return (
    <div className="py-16 text-center text-[13px]" style={{ color: t.textSub }}>{strings.noMatch}</div>
  )

  return (
    <div className="rounded-[8px] overflow-hidden" style={{ border: `1px solid ${t.border}` }}>
      <div className="grid text-[9.5px] font-600 uppercase tracking-widest py-2.5"
        style={{ gridTemplateColumns: '32px 1fr 2fr 100px 100px 36px', background: t.tableHead, borderBottom: `1px solid ${t.border}`, color: t.textSub, direction: isRtl?'rtl':'ltr' }}>
        <div className="px-3">#</div>
        <div className="px-3">{strings.field}</div>
        <div className="px-3">{strings.extractedValue}</div>
        <div className="px-3">{strings.confidence}</div>
        <div className="px-3">{strings.statusCol}</div>
        <div />
      </div>

      {fields.map((field, idx) => {
        const isOpen = expanded === field.id
        const rowBg  = idx % 2 === 0 ? t.rowEven : t.rowOdd
        const label  = isRtl ? field.labelAr : field.label
        const value  = isRtl ? field.valueAr  : field.value
        return (
          <div key={field.id} style={{ direction: isRtl?'rtl':'ltr' }}>
            <div className="grid items-center cursor-pointer select-none"
              style={{ gridTemplateColumns: '32px 1fr 2fr 100px 100px 36px', background: rowBg, transition: 'background .12s' }}
              onMouseEnter={e => (e.currentTarget as HTMLElement).style.background = t.rowHover}
              onMouseLeave={e => (e.currentTarget as HTMLElement).style.background = rowBg}
              onClick={() => setExpanded(p => p === field.id ? null : field.id)}>
              <div className="px-3 py-3 text-[10px] tabular-nums" style={{ color: t.textFaint }}>{field.id}</div>
              <div className="px-3 py-3">
                <div className="text-[12px] font-500 leading-snug" style={{ color: t.text }}>{label}</div>
                {field.pageRef && (
                  <div className={`flex items-center gap-1 mt-0.5 text-[10px] ${isRtl?'flex-row-reverse':''}`} style={{ color: '#2563EB' }}>
                    <Icon.PageRef />{field.pageRef}
                  </div>
                )}
              </div>
              <div className="px-3 py-3">
                {value
                  ? <span className="text-[12px] leading-snug" style={{ color: t.text }}>{value}</span>
                  : <span className="text-[12px] italic" style={{ color: t.textSub }}>{strings.notSpecified}</span>}
              </div>
              <div className="px-3 py-3">
                <ConfBadge c={field.confidence} pct={field.confidencePct}
                  reason={isRtl ? field.confidenceReasonAr : field.confidenceReason}
                  dark={dark} lang={lang} />
              </div>
              <div className="px-3 py-3"><StatusBadge s={field.status} dark={dark} lang={lang} /></div>
              <div className="flex items-center justify-center pr-3 pl-1">
                <span style={{ color: t.textSub }}><Icon.Chevron open={isOpen} /></span>
              </div>
            </div>

            {isOpen && (
              <div className="px-4 pb-3 pt-2" style={{ background: rowBg, borderTop: `1px solid ${t.border}` }}>
                <EvidencePanel field={field} dark={dark} lang={lang}
                  onClose={() => setExpanded(null)} onAskAI={onAskAI} />
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

// ── Agent page ────────────────────────────────────────────────────────────────

const SEV_CFG: Record<string, { dot: string; textL: string; textD: string; bgL: string; bgD: string; bdL: string; bdD: string }> = {
  critical: { dot:'bg-red-500',    textL:'text-red-700',    textD:'text-red-400',    bgL:'bg-red-50',    bgD:'bg-red-900/20',    bdL:'border-red-200',    bdD:'border-red-700' },
  high:     { dot:'bg-orange-500', textL:'text-orange-700', textD:'text-orange-400', bgL:'bg-orange-50', bgD:'bg-orange-900/20', bdL:'border-orange-200', bdD:'border-orange-700' },
  medium:   { dot:'bg-amber-500',  textL:'text-amber-700',  textD:'text-amber-400',  bgL:'bg-amber-50',  bgD:'bg-amber-900/20',  bdL:'border-amber-200',  bdD:'border-amber-700' },
  low:      { dot:'bg-blue-400',   textL:'text-blue-700',   textD:'text-blue-400',   bgL:'bg-blue-50',   bgD:'bg-blue-900/20',   bdL:'border-blue-200',   bdD:'border-blue-700' },
}

function SeverityBadge({ s, dark }: { s: string; dark: boolean }) {
  const cfg = SEV_CFG[s] ?? SEV_CFG.low
  return (
    <span className={`text-[10px] font-700 uppercase tracking-wide border rounded-[4px] px-2 py-0.5 ${dark ? `${cfg.textD} ${cfg.bgD} ${cfg.bdD}` : `${cfg.textL} ${cfg.bgL} ${cfg.bdL}`}`}>
      {s}
    </span>
  )
}

function FindingCard({ finding, dark, lang, onAskAI }: {
  finding: AgentFinding; dark: boolean; lang: Lang; onAskAI: (q: string) => void
}) {
  const [open, setOpen] = useState(false)
  const [srcOpen, setSrcOpen] = useState(false)
  const t = tk(dark)
  const strings = tr(lang)
  const isRtl = lang === 'ar'
  const title   = isRtl ? finding.titleAr   : finding.title
  const explanation = isRtl ? finding.explanationAr : finding.explanation
  const whyItMatters = isRtl ? finding.whyItMattersAr : finding.whyItMatters
  const cfg = SEV_CFG[finding.severity] ?? SEV_CFG.low

  const typeColor   = finding.type === 'confirmed' ? '#EF4444' : '#F59E0B'
  const typeTextEn  = finding.type === 'confirmed' ? strings.confirmedIssue : strings.potentialIssue
  const catLabel    = (strings.agentCatLabels as Record<string,string>)[finding.category] ?? finding.category

  return (
    <div className="rounded-[8px] overflow-hidden transition-colors"
      style={{ background: t.panelBg, border: `1px solid ${t.border}` }}>
      {/* Card header */}
      <div className={`px-4 py-3 cursor-pointer select-none flex items-start justify-between gap-3 ${isRtl?'flex-row-reverse':''}`}
        onClick={() => setOpen(p => !p)}>
        <div className={`flex items-start gap-3 min-w-0 ${isRtl?'flex-row-reverse':''}`}>
          {/* Severity color stripe */}
          <div className={`w-1 self-stretch rounded-full shrink-0 ${cfg.dot}`} />
          <div className="min-w-0">
            <div className={`flex items-center gap-2 flex-wrap mb-1 ${isRtl?'flex-row-reverse':''}`}>
              <SeverityBadge s={finding.severity} dark={dark} />
              <span className="text-[10.5px] font-500 px-2 py-0.5 rounded-[4px]"
                style={{ color: typeColor, background: dark?'rgba(0,0,0,.3)':'rgba(0,0,0,.04)', border: `1px solid ${typeColor}33` }}>
                {typeTextEn}
              </span>
              <span className="text-[10px]" style={{ color: t.textSub }}>{catLabel}</span>
            </div>
            <div className="text-[13px] font-600 leading-snug" style={{ color: t.text, textAlign: isRtl?'right':'left' }}>{title}</div>
            <div className={`flex items-center gap-1.5 mt-1.5 ${isRtl?'flex-row-reverse':''}`}>
              <ConfBadge c={finding.confidence} pct={finding.confidencePct} dark={dark} lang={lang} />
              {finding.sources.slice(0,2).map((src, i) => (
                <span key={i} className={`flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded-[4px] ${isRtl?'flex-row-reverse':''}`}
                  style={{ color: '#2563EB', background: dark?'#172035':'#EEF5FF', border: `1px solid ${dark?'#1E3A6A':'#BFDBFE'}` }}>
                  <Icon.PageRef />{strings.sourcePage} {src.page}
                </span>
              ))}
            </div>
          </div>
        </div>
        <span style={{ color: t.textSub }} className="shrink-0 mt-0.5"><Icon.Chevron open={open} /></span>
      </div>

      {/* Expanded body */}
      {open && (
        <div className="px-4 pb-4 space-y-3" style={{ borderTop: `1px solid ${t.border}` }}>
          <div className="pt-3 text-[12.5px] leading-relaxed" style={{ color: t.textSub, textAlign: isRtl?'right':'left' }}>
            {explanation}
          </div>

          <div className="rounded-[6px] p-3" style={{ background: dark?'#0C1525':'#FFF8F0', border: `1px solid ${dark?'#2A1A00':'#FED7AA'}` }}>
            <div className="text-[10px] font-700 uppercase tracking-widest mb-1" style={{ color: '#F59E0B', textAlign: isRtl?'right':'left' }}>
              {strings.whyItMatters}
            </div>
            <p className="text-[12px] leading-relaxed" style={{ color: t.text, textAlign: isRtl?'right':'left' }}>{whyItMatters}</p>
          </div>

          {/* Sources */}
          <div>
            <button onClick={() => setSrcOpen(p => !p)}
              className={`flex items-center gap-2 text-[11.5px] font-600 mb-2 ${isRtl?'flex-row-reverse':''}`}
              style={{ color: '#2563EB' }}>
              <Icon.PageRef /> {strings.viewSources}
              <span><Icon.Chevron open={srcOpen} /></span>
            </button>
            {srcOpen && finding.sources.map((src, i) => {
              const sectionLabel = isRtl ? (src.sectionAr || src.section) : src.section
              const quoteText    = isRtl ? (src.quoteAr    || src.quote)   : src.quote
              return (
                <div key={i} className="rounded-[6px] p-3 mb-2"
                  style={{ background: t.evidenceBg, border: `1px solid ${dark?'#1A3060':'#C5D8F8'}`, textAlign: isRtl?'right':'left' }}>
                  <div className={`flex items-center gap-2 mb-1.5 text-[11px] font-600 ${isRtl?'flex-row-reverse':''}`} style={{ color: '#2563EB' }}>
                    <Icon.PageRef />
                    {strings.sourcePage} {src.page}
                    {sectionLabel && <span style={{ color: t.textSub }}>— {sectionLabel}</span>}
                  </div>
                  <blockquote className="text-[12px] italic leading-relaxed"
                    style={{ [isRtl?'borderRight':'borderLeft']: '2px solid #2563EB', [isRtl?'paddingRight':'paddingLeft']: 10, color: t.textSub }}>
                    "{quoteText}"
                  </blockquote>
                </div>
              )
            })}
          </div>

          <button onClick={() => onAskAI(lang === 'ar'
            ? `أخبرني المزيد عن: ${finding.titleAr}`
            : `Tell me more about this finding: ${finding.title}`)}
            className={`flex items-center gap-1.5 text-[11px] font-500 px-2.5 py-1.5 rounded-[5px] transition-colors ${isRtl?'flex-row-reverse':''}`}
            style={{ background: dark?'#172035':'#EEF5FF', color: '#2563EB', border: `1px solid ${dark?'#1E3A6A':'#BFDBFE'}` }}>
            <Icon.AskAI /> {lang === 'ar' ? 'اسأل المساعد عن هذه النتيجة' : 'Ask AI about this finding'}
          </button>
        </div>
      )}
    </div>
  )
}

function AgentPage({ dark, lang, findings, isRunning, hasRun, onRun, onAskAI }: {
  dark: boolean; lang: Lang; findings: AgentFinding[]
  isRunning: boolean; hasRun: boolean; onRun: () => void; onAskAI: (q: string, switchView?: boolean) => void
}) {
  const t = tk(dark)
  const strings = tr(lang)
  const isRtl = lang === 'ar'
  const font = isRtl ? 'Cairo, sans-serif' : 'Inter, sans-serif'
  const [sevFilter,    setSevFilter]    = useState<SeverityFilter>('all')
  const [catFilter,    setCatFilter]    = useState<AgentCatFilter>('all')
  const [agentProgress, setAgentProgress] = useState(0)

  useEffect(() => {
    if (!isRunning) { setAgentProgress(0); return }
    const t2 = setInterval(() => setAgentProgress(p => Math.min(p + Math.random() * 8 + 3, 98)), 200)
    return () => clearInterval(t2)
  }, [isRunning])

  const critical = findings.filter(f => f.severity === 'critical').length
  const high     = findings.filter(f => f.severity === 'high').length
  const medium   = findings.filter(f => f.severity === 'medium').length
  const low      = findings.filter(f => f.severity === 'low').length
  const potential = findings.filter(f => f.type === 'potential').length

  const filtered = findings.filter(f => {
    if (sevFilter !== 'all' && f.severity !== sevFilter) return false
    if (catFilter !== 'all' && f.category !== catFilter) return false
    return true
  })

  const agentSteps = strings.agentProcessingSteps
  const activeStep = isRunning ? Math.min(Math.floor((agentProgress / 100) * (agentSteps.length - 1)), agentSteps.length - 2) : (hasRun ? agentSteps.length - 1 : 0)

  const KPI_TILES = [
    { label: strings.totalFindings, value: findings.length, color: t.text },
    { label: strings.criticalLabel, value: critical, color: '#EF4444' },
    { label: strings.highLabel,     value: high,     color: '#F97316' },
    { label: strings.mediumLabel,   value: medium,   color: '#F59E0B' },
    { label: strings.lowLabel,      value: low,      color: '#60A5FA' },
    { label: strings.potentialGaps, value: potential, color: '#8B5CF6' },
  ]

  return (
    <div className="h-full overflow-y-auto" style={{ background: t.pageBg, fontFamily: font }}>
      <div className="p-5 space-y-4 max-w-5xl">
        {/* Header */}
        <div className={`flex items-start justify-between gap-4 ${isRtl?'flex-row-reverse':''}`}>
          <div className={isRtl?'text-right':''}>
            <h2 className="text-[16px] font-700" style={{ color: t.text }}>{strings.agentTitle}</h2>
            <p className="text-[12px] mt-0.5" style={{ color: t.textSub }}>{strings.agentSubtitle}</p>
          </div>
          {!hasRun && !isRunning && (
            <button onClick={onRun}
              className={`flex items-center gap-2 px-4 py-2.5 rounded-[7px] text-[13px] font-600 text-white shrink-0 ${isRtl?'flex-row-reverse':''}`}
              style={{ background: '#2563EB' }}>
              <Icon.Agent /> {strings.agentRun}
            </button>
          )}
        </div>

        {/* Processing animation */}
        {(isRunning || hasRun) && (
          <div className="rounded-[10px] p-5 space-y-4" style={{ background: t.panelBg, border: `1px solid ${t.border}` }}>
            <div className={`flex items-center justify-between ${isRtl?'flex-row-reverse':''}`}>
              <div className={`flex items-center gap-2.5 ${isRtl?'flex-row-reverse':''}`}>
                <div className={`w-2 h-2 rounded-full ${isRunning ? 'bg-[#2563EB] animate-pulse' : 'bg-emerald-500'}`} />
                <span className="text-[13px] font-600" style={{ color: t.text }}>
                  {isRunning ? strings.agentRunning : strings.agentDone}
                </span>
              </div>
              {isRunning && <span className="text-[13px] font-700 tabular-nums" style={{ color: '#2563EB' }}>{Math.round(agentProgress)}%</span>}
            </div>
            {isRunning && (
              <div className="h-1.5 rounded-full overflow-hidden" style={{ background: t.tagBg }}>
                <div className="h-full rounded-full bg-[#2563EB] transition-all duration-300" style={{ width: `${agentProgress}%` }} />
              </div>
            )}
            <div className="space-y-2">
              {agentSteps.map((step, i) => {
                const done   = hasRun || i < activeStep
                const active = isRunning && i === activeStep
                return (
                  <div key={i} className={`flex items-center gap-3 ${isRtl?'flex-row-reverse':''}`}>
                    <div className="w-5 h-5 rounded-full flex items-center justify-center shrink-0 transition-all"
                      style={{ background: done ? '#2563EB' : active ? 'rgba(37,99,235,.15)' : t.tagBg, border: active ? '2px solid #2563EB' : 'none' }}>
                      {done   && <span className="text-white"><Icon.Check /></span>}
                      {active && <div className="w-1.5 h-1.5 rounded-full bg-[#2563EB] animate-pulse" />}
                    </div>
                    <span className="text-[12px]" style={{ color: done || active ? t.text : t.textSub, fontWeight: active?600:400 }}>{step}</span>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {hasRun && (
          <>
            {/* KPI strip */}
            <div className="grid gap-3" style={{ gridTemplateColumns: 'repeat(6, 1fr)' }}>
              {KPI_TILES.map(tile => (
                <div key={tile.label} className="rounded-[8px] px-3 py-3"
                  style={{ background: t.panelBg, border: `1px solid ${t.border}`, textAlign: isRtl?'right':'left' }}>
                  <div className="text-[9px] font-600 uppercase tracking-widest mb-1" style={{ color: t.textSub }}>{tile.label}</div>
                  <div className="text-[24px] font-700 tabular-nums" style={{ color: tile.color }}>{tile.value}</div>
                </div>
              ))}
            </div>

            {/* Filter row */}
            <div className={`flex items-center gap-2 flex-wrap ${isRtl?'flex-row-reverse':''}`}>
              {/* Severity filters */}
              {(['all','critical','high','medium','low'] as SeverityFilter[]).map(s => {
                const label = s === 'all' ? strings.allFindings
                  : s === 'critical' ? strings.criticalLabel
                  : s === 'high'     ? strings.highLabel
                  : s === 'medium'   ? strings.mediumLabel
                  : strings.lowLabel
                return (
                  <button key={s} onClick={() => setSevFilter(s)}
                    className="text-[11px] font-500 px-2.5 py-1 rounded-[6px] transition-colors"
                    style={{ background: sevFilter===s ? '#2563EB' : t.chipBg, color: sevFilter===s ? '#fff' : t.textSub, border: `1px solid ${sevFilter===s ? '#2563EB' : t.border}` }}>
                    {label}
                  </button>
                )
              })}
              <div className="h-5 w-px mx-1" style={{ background: t.border }} />
              {/* Category filter */}
              <select value={catFilter} onChange={e => setCatFilter(e.target.value as AgentCatFilter)}
                className="text-[11px] font-500 px-2.5 py-1 rounded-[6px] outline-none"
                style={{ background: t.chipBg, color: t.textSub, border: `1px solid ${t.border}` }}>
                <option value="all">{strings.allFindings}</option>
                {Object.entries(strings.agentCatLabels).map(([k, v]) => (
                  <option key={k} value={k}>{v}</option>
                ))}
              </select>
              <span className={`${isRtl?'mr-auto':'ml-auto'} text-[11px] tabular-nums`} style={{ color: t.textSub }}>
                {filtered.length} / {findings.length}
              </span>
            </div>

            {/* Finding cards */}
            {filtered.length === 0
              ? <div className="py-12 text-center text-[13px]" style={{ color: t.textSub }}>{strings.agentEmpty}</div>
              : <div className="space-y-3">
                  {filtered.map(f => (
                    <FindingCard key={f.id} finding={f} dark={dark} lang={lang}
                      onAskAI={q => onAskAI(q, true)} />
                  ))}
                </div>
            }
          </>
        )}

        {/* Empty state — not run yet */}
        {!hasRun && !isRunning && (
          <div className="rounded-[10px] py-20 flex flex-col items-center gap-5"
            style={{ background: t.panelBg, border: `2px dashed ${t.border}` }}>
            <div className="w-14 h-14 rounded-[12px] flex items-center justify-center"
              style={{ background: dark?'#172035':'#EEF5FF', border: `1px solid ${t.border}` }}>
              <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
                <circle cx="14" cy="12" r="6" stroke="#2563EB" strokeWidth="1.8"/>
                <path d="M5 25c0-4.97 4.03-9 9-9s9 4.03 9 9" stroke="#2563EB" strokeWidth="1.8" strokeLinecap="round"/>
                <path d="M14 4v1.5M14 20v1.5M22 12h-1.5M7.5 12H6" stroke="#2563EB" strokeWidth="1.5" strokeLinecap="round"/>
              </svg>
            </div>
            <div className="text-center space-y-1.5">
              <p className="text-[15px] font-600" style={{ color: t.text }}>{strings.agentTitle}</p>
              <p className="text-[12.5px] max-w-sm" style={{ color: t.textSub }}>{strings.agentSubtitle}</p>
            </div>
            <button onClick={onRun}
              className={`flex items-center gap-2 px-5 py-2.5 rounded-[7px] text-[13px] font-600 text-white ${isRtl?'flex-row-reverse':''}`}
              style={{ background: '#2563EB' }}>
              <Icon.Agent /> {strings.agentRun}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

// ── Chat panel ────────────────────────────────────────────────────────────────

function ChatPanel({ dark, lang, initialQ, documentId }: {
  dark: boolean; lang: Lang; initialQ: string | null; documentId: string | null
}) {
  const t = tk(dark)
  const strings = tr(lang)
  const isRtl = lang === 'ar'
  const font = isRtl ? 'Cairo, sans-serif' : 'Inter, sans-serif'

  const [messages, setMessages] = useState<ChatMessage[]>([
    { id: 0, role: 'assistant', text: strings.hiMsg }
  ])
  const [input, setInput] = useState('')
  const [typing, setTyping] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const historyRef = useRef<{ role: 'user' | 'assistant'; text: string }[]>([])

  useLayoutEffect(() => { if (initialQ) send(initialQ) }, [initialQ]) // eslint-disable-line react-hooks/exhaustive-deps
  useEffect(() => { setMessages([{ id: 0, role: 'assistant', text: strings.hiMsg }]); historyRef.current = [] }, [lang]) // eslint-disable-line react-hooks/exhaustive-deps

  const scrollDown = () => setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 50)

  async function send(text: string) {
    if (!text.trim() || typing) return
    const userMsg: ChatMessage = { id: Date.now(), role: 'user', text: text.trim() }
    setMessages(m => [...m, userMsg])
    setInput('')
    setTyping(true)
    scrollDown()

    try {
      // ── API CALL ─────────────────────────────────────────────────────────
      // Swap sendChatMessage in src/api.ts for your real endpoint.
      const resp = await sendChatMessage({
        documentId: documentId ?? 'demo',
        message: text.trim(),
        history: historyRef.current,
        lang,
      })
      // ─────────────────────────────────────────────────────────────────────
      historyRef.current = [...historyRef.current, { role: 'user', text: text.trim() }, { role: 'assistant', text: resp.text }]
      setMessages(m => [...m, { id: Date.now() + 1, role: 'assistant', ...resp }])
    } catch {
      setMessages(m => [...m, { id: Date.now() + 1, role: 'assistant', text: 'An error occurred. Please try again.' }])
    } finally {
      setTyping(false)
      scrollDown()
    }
  }

  const renderText = (text: string) => text.split('\n').map((line, i) => (
    <p key={i} dangerouslySetInnerHTML={{ __html: line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>') || '<br/>' }} className="leading-snug" />
  ))

  return (
    <div className="flex flex-col h-full transition-colors duration-200" style={{ background: t.panelBg, fontFamily: font, direction: isRtl?'rtl':'ltr' }}>
      <div className={`px-4 py-3 shrink-0 flex items-center gap-2.5 ${isRtl?'flex-row-reverse':''}`}
        style={{ borderBottom: `1px solid ${t.border}` }}>
        <div className="w-7 h-7 rounded-[6px] bg-[#2563EB] flex items-center justify-center shrink-0"><Icon.Sparkle /></div>
        <div className={isRtl?'text-right':''}>
          <div className="text-[13px] font-600" style={{ color: t.text }}>{strings.rfpAssistant}</div>
          <div className="text-[10px]" style={{ color: documentId ? '#10B981' : t.textSub }}>
            {documentId ? strings.onlineDocLoaded : '● Waiting for document…'}
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
        {messages.map(msg => (
          <div key={msg.id} className={`flex ${msg.role==='user' ? (isRtl?'justify-start':'justify-end') : (isRtl?'justify-end':'justify-start')}`}>
            <div className="max-w-[90%] space-y-1.5">
              {msg.role === 'assistant' && (
                <div className="w-4 h-4 rounded-full bg-[#2563EB] flex items-center justify-center mb-0.5">
                  <Icon.Sparkle />
                </div>
              )}
              <div className="rounded-[8px] px-3 py-2.5 text-[12.5px] space-y-0.5"
                style={{ background: msg.role==='user' ? t.chatUserBg : t.chatAIBg, color: t.text, border: `1px solid ${msg.role==='user' ? (dark?'#1E3A6A':'#BFDBFE') : t.border}`, textAlign: isRtl?'right':'left' }}>
                {renderText(msg.text)}
              </div>
              {msg.refs && (
                <div className={`flex flex-wrap gap-1 ${isRtl?'flex-row-reverse':''}`}>
                  {msg.refs.map((r, i) => (
                    <span key={i} className={`flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded-[4px] cursor-pointer ${isRtl?'flex-row-reverse':''}`}
                      style={{ color: '#2563EB', background: dark?'#172035':'#EEF5FF', border: `1px solid ${dark?'#1E3A6A':'#BFDBFE'}` }}>
                      <Icon.PageRef />{r}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {typing && (
          <div className={`flex ${isRtl?'justify-end':'justify-start'}`}>
            <div className="rounded-[8px] px-3 py-2.5" style={{ background: t.chatAIBg, border: `1px solid ${t.border}` }}>
              <div className="flex gap-1 items-center h-4">
                {[0,1,2].map(i => <div key={i} className="w-1.5 h-1.5 rounded-full bg-[#2563EB] animate-bounce" style={{ animationDelay: `${i*150}ms` }} />)}
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {messages.length <= 1 && (
        <div className="px-4 pb-2 shrink-0">
          <div className={`text-[10px] font-600 uppercase tracking-widest mb-2 ${isRtl?'text-right':''}`} style={{ color: t.textSub }}>{strings.suggestedQ}</div>
          <div className={`flex flex-wrap gap-1.5 ${isRtl?'flex-row-reverse':''}`}>
            {strings.quickPrompts.map(p => (
              <button key={p} onClick={() => send(p)}
                className="text-[11px] font-500 px-2.5 py-1.5 rounded-[6px] text-left transition-all hover:border-[#2563EB] hover:text-[#2563EB]"
                style={{ background: t.tagBg, color: t.textSub, border: `1px solid ${t.border}` }}>{p}</button>
            ))}
          </div>
        </div>
      )}

      <div className="px-4 py-3 shrink-0" style={{ borderTop: `1px solid ${t.border}` }}>
        <div className={`flex items-end gap-2 rounded-[8px] px-3 py-2 ${isRtl?'flex-row-reverse':''}`}
          style={{ background: t.inputBg, border: `1px solid ${t.border}` }}>
          <textarea rows={1} value={input} onChange={e => setInput(e.target.value)}
            onKeyDown={e => { if (e.key==='Enter'&&!e.shiftKey){e.preventDefault();send(input)} }}
            placeholder={strings.chatPlaceholder}
            className="flex-1 resize-none bg-transparent text-[12.5px] leading-relaxed outline-none"
            style={{ color: t.text, maxHeight: 80, textAlign: isRtl?'right':'left', direction: isRtl?'rtl':'ltr' }} />
          <button onClick={() => send(input)} disabled={!input.trim()||typing}
            className="w-7 h-7 rounded-[6px] flex items-center justify-center shrink-0 text-white disabled:opacity-40 hover:bg-blue-700 transition-colors"
            style={{ background: '#2563EB' }}><Icon.Send /></button>
        </div>
        <p className={`text-[10px] mt-1.5 ${isRtl?'text-right':''}`} style={{ color: t.textFaint }}>{strings.chatDisclaimer}</p>
      </div>
    </div>
  )
}

// ─────────────────────────────────────────────────────────────────────────────
// ROOT APP
// ─────────────────────────────────────────────────────────────────────────────

export default function App() {
  // ── UI state ────────────────────────────────────────────────────────────────
  const [lang,       setLang]       = useState<Lang>('en')
  const [themeMode,  setThemeMode]  = useState<ThemeMode>('system')
  const [dark,       setDark]       = useState(() => resolveTheme('system'))
  const [view,       setView]       = useState<AppView>('extraction')
  const [catFilter,  setCatFilter]  = useState<Category | 'all'>('all')
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all')
  const [confFilter, setConfFilter] = useState<ConfFilter>('all')
  const [search,     setSearch]     = useState('')
  const [chatQ,      setChatQ]      = useState<string | null>(null)

  // ── Extraction state ────────────────────────────────────────────────────────
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([])
  const [progress,      setProgress]      = useState(0)
  const [isExtracting,  setIsExtracting]  = useState(false)
  const [result,        setResult]        = useState<ExtractionResult | null>(null)
  const [documentId,    setDocumentId]    = useState<string | null>(null)

  // ── Agent state ──────────────────────────────────────────────────────────────
  const [agentFindings,  setAgentFindings]  = useState<AgentFinding[]>([])
  const [agentRunning,   setAgentRunning]   = useState(false)
  const [agentHasRun,    setAgentHasRun]    = useState(false)

  const t = tk(dark)
  const strings = tr(lang)
  const isRtl = lang === 'ar'
  const font = isRtl ? 'Cairo, sans-serif' : 'Inter, sans-serif'

  const fields = result?.fields ?? []

  // ── Theme resolution ────────────────────────────────────────────────────────
  useEffect(() => {
    if (themeMode === 'system') {
      const mq = window.matchMedia('(prefers-color-scheme: dark)')
      setDark(mq.matches)
      const handler = (e: MediaQueryListEvent) => setDark(e.matches)
      mq.addEventListener('change', handler)
      return () => mq.removeEventListener('change', handler)
    } else {
      setDark(themeMode === 'dark')
    }
  }, [themeMode])

  useEffect(() => { document.body.style.background = t.pageBg }, [t.pageBg])

  // ── Upload → extract flow ───────────────────────────────────────────────────
  const handleUpload = useCallback(async (files: File[]) => {
    setUploadedFiles(files.map(f => ({ name: f.name, size: f.size })))
    setIsExtracting(true)
    setProgress(0)
    setResult(null)

    try {
      // Step 1 — upload
      // 🔌 src/api.ts → uploadDocument()
      const uploadResp = await uploadDocument(files)
      setDocumentId(uploadResp.documentId)

      // Step 2 — animate progress while polling
      let p = 0
      const timer = setInterval(() => {
        p = Math.min(p + Math.random() * 10 + 4, 95)
        setProgress(Math.round(p))
      }, 220)

      // Step 3 — poll until done
      // 🔌 src/api.ts → getExtractionStatus()
      let done = false
      while (!done) {
        await new Promise(r => setTimeout(r, 1000))
        const status = await getExtractionStatus(uploadResp.documentId)
        done = status.done
      }

      clearInterval(timer)
      setProgress(100)

      // Step 4 — fetch fields
      // 🔌 src/api.ts → getExtractedFields()
      const extracted = await getExtractedFields(uploadResp.documentId)
      setTimeout(() => {
        setResult(extracted)
        setIsExtracting(false)
      }, 500)
    } catch (err) {
      console.error('Extraction error:', err)
      setIsExtracting(false)
    }
  }, [])

  const handleReset = () => {
    setResult(null); setDocumentId(null); setUploadedFiles([])
    setProgress(0); setIsExtracting(false); setSearch('')
    setCatFilter('all'); setStatusFilter('all'); setConfFilter('all')
    setAgentFindings([]); setAgentRunning(false); setAgentHasRun(false)
  }

  const handleAskAI = (q: string, switchToChat = true) => {
    setChatQ(q)
    if (switchToChat) setView('chat')
    setTimeout(() => setChatQ(null), 100)
  }

  const handleRunAgent = async () => {
    if (!documentId) return
    setAgentRunning(true)
    try {
      const findings = await runAgentReview(documentId)
      setAgentFindings(findings)
    } catch (err) {
      console.error('Agent review failed:', err)
      setAgentFindings([])
    } finally {
      setAgentRunning(false)
      setAgentHasRun(true)
    }
  }

  // ── Filtering ────────────────────────────────────────────────────────────────
  const filtered = fields.filter(f => {
    if (catFilter !== 'all' && f.category !== catFilter) return false
    if (statusFilter !== 'all' && f.status !== statusFilter) return false
    if (confFilter  !== 'all' && f.confidence !== confFilter) return false
    const q = search.toLowerCase()
    if (q) {
      const inLabel = (isRtl ? f.labelAr : f.label).toLowerCase().includes(q)
      const inValue = ((isRtl ? f.valueAr : f.value) ?? '').toLowerCase().includes(q)
      if (!inLabel && !inValue) return false
    }
    return true
  })

  const isDone = result !== null
  const isIdle = !isExtracting && !isDone

  // ── Render ───────────────────────────────────────────────────────────────────
  return (
    <div className="flex h-screen overflow-hidden transition-colors duration-200"
      style={{ background: t.pageBg, color: t.text, direction: isRtl?'rtl':'ltr', fontFamily: font }}>

      <Sidebar view={view} onView={setView} catFilter={catFilter} onCat={setCatFilter}
        statusFilter={statusFilter} onStatus={setStatusFilter} dark={dark} lang={lang} fields={fields} />

      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <div className="shrink-0 flex items-center justify-between px-5 py-3"
          style={{ background: t.headerBg, borderBottom: `1px solid ${t.border}` }}>
          <div>
            <h1 className="text-[15px] font-700 leading-tight" style={{ color: t.text }}>
              {view === 'chat' ? strings.rfpAssistant : view === 'agent' ? strings.agentTitle : strings.fieldExtraction}
            </h1>
            {isDone && (
              <p className="text-[11px] mt-0.5" style={{ color: t.textSub }}>
                {uploadedFiles.map(f=>f.name).join(', ')} · {fields.length} {strings.fields} · {filtered.length} {strings.fieldsShown}
              </p>
            )}
          </div>

          <div className={`flex items-center gap-2 ${isRtl?'flex-row-reverse':''}`}>
            {/* Search */}
            {view === 'extraction' && isDone && (
              <div className="relative">
                <span className={`absolute ${isRtl?'right-2.5':'left-2.5'} top-1/2 -translate-y-1/2`} style={{ color: t.textSub }}><Icon.Search /></span>
                <input type="text" placeholder={strings.searchFields} value={search} onChange={e => setSearch(e.target.value)}
                  className="py-1.5 text-[12px] rounded-[6px] outline-none w-44"
                  style={{ paddingLeft: isRtl?12:28, paddingRight: isRtl?28:12, background: t.inputBg, border: `1px solid ${t.border}`, color: t.text, direction: isRtl?'rtl':'ltr' }} />
              </div>
            )}

            {/* Language switcher */}
            <div className="flex rounded-[6px] overflow-hidden" style={{ border: `1px solid ${t.border}` }}>
              {(['en','ar'] as Lang[]).map(l => (
                <button key={l} onClick={() => setLang(l)}
                  className={`flex items-center gap-1.5 px-2.5 py-1.5 text-[11px] font-500 transition-colors ${isRtl?'flex-row-reverse':''}`}
                  style={{ background: lang===l ? '#2563EB' : t.chipBg, color: lang===l ? '#fff' : t.textSub, fontFamily: l==='ar'?'Cairo, sans-serif':'Inter, sans-serif' }}>
                  <Icon.Globe />{l === 'en' ? strings.english : strings.arabic}
                </button>
              ))}
            </div>

            {/* Theme switcher */}
            <div className="flex rounded-[6px] overflow-hidden" style={{ border: `1px solid ${t.border}` }}>
              {([['light', <Icon.Sun />], ['dark', <Icon.Moon />], ['system', <Icon.Monitor />]] as [ThemeMode, JSX.Element][]).map(([mode, icon]) => (
                <button key={mode} onClick={() => setThemeMode(mode)} title={(strings as unknown as Record<string,string>)[`theme${mode.charAt(0).toUpperCase()}${mode.slice(1)}`]}
                  className="w-8 h-8 flex items-center justify-center transition-colors"
                  style={{ background: themeMode===mode ? '#2563EB' : t.chipBg, color: themeMode===mode ? '#fff' : t.textSub }}>
                  {icon}
                </button>
              ))}
            </div>

            {isDone && (
              <button onClick={handleReset}
                className="text-[12px] font-500 px-3 py-1.5 rounded-[6px] transition-colors"
                style={{ color: t.textSub, background: t.chipBg, border: `1px solid ${t.border}` }}>
                {strings.newUpload}
              </button>
            )}
          </div>
        </div>

        {/* Content area */}
        <div className="flex-1 overflow-hidden flex">
          {/* Extraction workspace */}
          <div className={`overflow-y-auto transition-colors ${view!=='extraction' ? 'hidden' : 'flex-1'}`}
            style={{ background: t.pageBg }}>
            <div className="p-5 space-y-4">
              {isIdle && <UploadZone onUpload={handleUpload} dark={dark} lang={lang} />}

              {isExtracting && (
                <Processing files={uploadedFiles} progress={progress} dark={dark} lang={lang} />
              )}

              {isDone && (
                <>
                  <KpiRow dark={dark} lang={lang} fields={fields} pageCount={result?.pageCount ?? 0} />

                  {/* Confidence filter chips */}
                  <div className={`flex items-center gap-2 flex-wrap ${isRtl?'flex-row-reverse':''}`}>
                    {(['all','high','medium','low'] as ConfFilter[]).map(cf => (
                      <button key={cf} onClick={() => setConfFilter(cf)}
                        className="text-[11px] font-500 px-2.5 py-1 rounded-[6px] transition-colors"
                        style={{ background: confFilter===cf ? '#2563EB' : t.chipBg, color: confFilter===cf ? '#fff' : t.textSub, border: `1px solid ${confFilter===cf ? '#2563EB' : t.border}` }}>
                        {cf==='all' ? strings.allConf : cf==='high' ? strings.high : cf==='medium' ? strings.medium : strings.low}
                      </button>
                    ))}
                    <span className={`${isRtl?'mr-auto':'ml-auto'} text-[11px] tabular-nums`} style={{ color: t.textSub }}>
                      {filtered.length} / {fields.length}
                    </span>
                  </div>

                  <ExtractionTable fields={filtered} dark={dark} lang={lang} onAskAI={handleAskAI} />
                  <EvalInsights dark={dark} lang={lang} fields={fields} />
                </>
              )}
            </div>
          </div>

          {/* Agent workspace */}
          <div className={`${view!=='agent' ? 'hidden' : 'flex-1 overflow-hidden'}`}>
            <AgentPage dark={dark} lang={lang} findings={agentFindings}
              isRunning={agentRunning} hasRun={agentHasRun}
              onRun={handleRunAgent}
              onAskAI={(q, sw) => handleAskAI(q, sw ?? true)} />
          </div>

          {/* Chat panel — always mounted so message history persists */}
          {(isDone || view === 'chat' || agentHasRun) && (
            <div className={view==='chat' ? 'flex-1 overflow-hidden' : 'w-[360px] shrink-0 overflow-hidden'}
              style={{ [isRtl?'borderRight':'borderLeft']: `1px solid ${t.border}`, display: view==='agent' ? 'none' : undefined }}>
              <ChatPanel dark={dark} lang={lang} initialQ={chatQ} documentId={documentId} />
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

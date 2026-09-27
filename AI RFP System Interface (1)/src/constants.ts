// ─────────────────────────────────────────────────────────────────────────────
// RFP Extract — Lookup Constants
// ─────────────────────────────────────────────────────────────────────────────
// Extraction, chat, and the agent review are all wired to the real backend
// (server.py) now - nothing in this file is mock data anymore.
// ─────────────────────────────────────────────────────────────────────────────

import type { Category } from './types'

// ── Category ordering (used by sidebar nav) ───────────────────────────────────

export const CATEGORY_ORDER: Category[] = [
  'deadline', 'contact', 'scope', 'requirements', 'evaluation', 'compliance',
]

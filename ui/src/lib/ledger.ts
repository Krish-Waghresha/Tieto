// Types for the ledger produced by reviewbot (Python). The UI renders ONLY from this data.

export type Grade = 'PROVEN' | 'MEASURED' | 'HEURISTIC' | 'ARGUED' | 'ABSTAINED' | 'UNSUPPORTED'
export type Tier = 'LIGHT' | 'STANDARD' | 'DEEP'

export interface Excerpt { start: number; lines: string[]; focus: [number, number]; insertion?: boolean }
export interface Snippet { path: string; lang: string; before: Excerpt | null; after: Excerpt | null }

export interface Fact {
  id: string; kind: string; grade: Grade; text: string; holds?: boolean | null; count?: number
  lines?: number[]; claims?: string[]; grade_note?: string
  field?: string; methods?: string[]; sites?: { line: number; method: string }[]
  method?: string; cond?: string; then_calls?: string[]; has_else?: boolean
}
export interface Test { name: string; outcome: string; message: string }
export interface Proof {
  id: string; title: string; grade: Grade; status: 'executed' | 'not_executed'; result: string; note?: string
  claims?: string[]; tests?: Test[]; command?: string; sdk?: string; limit?: string
}
export interface Decision {
  id: string; title: string; claims: string[]; facts?: string[]; before: string; after: string
  alternatives: string[]; rationale: string; trace: { to: string[]; status: string; note?: string }
  dimensions: Record<string, string>; recommended: string; recommendation_reason: string; evidence: Proof[]
}
export interface Finding {
  id: string; title: string; claims: string[]; facts: string[]; argument: string; status: string; grade: Grade
  fix_hint: string; evidence: Proof[]; severity?: string
}
export interface Abstention { id: string; kind: string; title: string; why: string; human_action: string; grade: Grade }
export interface Fired { rule: string; tier: Tier | null; where: string[]; detail: string; why: string; motivated_by: string; grade: Grade }
export interface QuizQ {
  id: string; kind: 'choice' | 'line' | 'free'; question: string; options?: string[]; answer?: number
  key_grade?: Grade; explain?: string
}
export interface Ledger {
  status_note: string
  pin: { repo: string; pr: number | string | null; base: string; head: string; pr_author: string; requirement_id: string
         upstream?: { repo?: string; head_sha?: string } }
  requirement: { id: string; acceptance_criteria: Record<string, string>; trace: Record<string, { by: string[]; proofs: string[]; note?: string }> }
  summary?: { what: string; verdict: string }
  owners?: { owner: string; role: string }[]
  triage: { tier: Tier; base_tier: Tier; fired: Fired[]; required_checks: { rule: string; check: string; status?: string; why: string; motivated_by: string; proofs?: string[] }[] }
  facts: Fact[]; proofs: Proof[]; decisions: Decision[]; findings: Finding[]; abstentions: Abstention[]
  coverage: { hunks: { id: string; added: number; removed: number; claimed_by: string[]; path: string; new_start: number }[]; unexplained: string[]; complete: boolean }
  scope: { decision: string; requirement_sites: number; reach: number; ratio: number; mismatch: boolean; grade: Grade; text: string }[]
  snippets: Record<string, Snippet>
  not_checked: string[]; what_to_do: { text: string; refs: string[] }[]; quiz: QuizQ[]
  grade_counts: Record<string, number>; open_items: string[]; dependent_items: string[]
  files: { path: string; repo_path: string }[]
  ledger_sha256: string
}

export interface AudioPayload { src: string | null; script: string }

function readJson<T>(id: string, fallback: T): T {
  const el = document.getElementById(id)
  const txt = el?.textContent ?? ''
  if (!txt || txt.startsWith('__')) return fallback
  return JSON.parse(txt) as T
}

export const ledger: Ledger = readJson<Ledger>('ledger', null as unknown as Ledger)
export const audio: AudioPayload = readJson<AudioPayload>('audio', { src: null, script: '' })

export const GRADE_ORDER: Grade[] = ['PROVEN', 'MEASURED', 'HEURISTIC', 'ARGUED', 'ABSTAINED', 'UNSUPPORTED']

export const isDependent = (d: Decision) => d.recommended.startsWith('follow_')
export const parentOf = (d: Decision) => d.recommended.slice('follow_'.length)

/** Decisions in reading order: policy decisions first, their dependents right after, then the rest. */
export function orderedDecisions(L: Ledger): Decision[] {
  const prim = L.decisions.filter(d => !isDependent(d))
  const open = prim.filter(d => d.recommended !== 'accept')
  const rest = prim.filter(d => d.recommended === 'accept')
  const out: Decision[] = []
  for (const d of [...open, ...rest]) {
    out.push(d, ...L.decisions.filter(x => isDependent(x) && parentOf(x) === d.id))
  }
  return out
}

export const fileName = (p: string) => p.split('/').pop() ?? p
export const hunkLabel = (id: string) => { const [p, l] = id.split('#L'); return `${fileName(p)}:${l}` }

export function sourceUrl(L: Ledger, hunkId: string): string | null {
  const [path, line] = hunkId.split('#L')
  const f = L.files.find(x => x.path === path)
  if (!L.pin.repo || !f || !/^[\w./-]+$/.test(f.repo_path)) return null
  return `https://github.com/${L.pin.repo}/blob/${L.pin.head}/${f.repo_path}#L${line}`
}

export function proofCounts(L: Ledger) {
  const ran = L.proofs.filter(p => p.status === 'executed')
  return { ran: ran.length, total: L.proofs.length, violated: ran.filter(p => p.result === 'VIOLATED').map(p => p.id) }
}

// ---- reviewer state → /sign text (must match reviewbot/sign.py) ----
export type DecisionPick = { value: 'accept' | 'request_change' | 'reject'; prefer?: string }
export type FindingPick = { value: 'valid' | 'invalid'; note?: string }
export type AbstPick = { value: 'resolved' | 'accept_risk' | 'defer' }
export interface ReviewState {
  decisions: Record<string, DecisionPick>
  findings: Record<string, FindingPick>
  abstentions: Record<string, AbstPick>
  quiz: Record<string, number | string>
  quizChecked: boolean
  couldBreak: string
  risk: string
  final?: 'approve' | 'request_changes' | 'reject'
}
export const emptyState = (): ReviewState => ({ decisions: {}, findings: {}, abstentions: {}, quiz: {}, quizChecked: false, couldBreak: '', risk: '' })

export function requiredItems(L: Ledger): string[] {
  return [...L.decisions.filter(d => !isDependent(d)).map(d => d.id), ...L.findings.map(f => f.id), ...L.abstentions.map(a => a.id)]
}
export function unresolved(L: Ledger, s: ReviewState): string[] {
  return requiredItems(L).filter(id => !(s.decisions[id] || s.findings[id] || s.abstentions[id]))
}
export function suggestedFinal(L: Ledger, s: ReviewState): 'approve' | 'request_changes' {
  if (unresolved(L, s).length) return 'request_changes'
  const blocking = Object.values(s.decisions).some(p => p.value !== 'accept')
    || Object.values(s.abstentions).some(p => p.value === 'defer')
    || L.findings.some(f => s.findings[f.id]?.value === 'valid')
  return blocking ? 'request_changes' : 'approve'
}
export function quizScore(L: Ledger, s: ReviewState): { right: number; total: number } {
  const keyed = L.quiz.filter(q => q.kind !== 'free' && typeof q.answer === 'number')
  return { right: keyed.filter(q => s.quiz[q.id] === q.answer).length, total: keyed.length }
}
const oneLine = (t: string) => t.replace(/[\r\n]+/g, ' ').slice(0, 400)

export function signText(L: Ledger, s: ReviewState): string {
  const final = s.final ?? suggestedFinal(L, s)
  const lines = ['/sign', `head: ${L.pin.head}`, `ledger: ${L.ledger_sha256.slice(0, 12)}`, `decision: ${final}`]
  for (const d of L.decisions.filter(d => !isDependent(d))) {
    const p = s.decisions[d.id]
    lines.push(`${d.id}: ${p?.value ?? 'UNRESOLVED'}`)
    if (p?.prefer) lines.push(`${d.id}_prefer: ${oneLine(p.prefer)}`)
  }
  for (const f of L.findings) {
    const p = s.findings[f.id]
    lines.push(`${f.id}: ${p?.value ?? 'UNRESOLVED'}`)
    if (p?.note) lines.push(`${f.id}_note: ${oneLine(p.note)}`)
  }
  for (const a of L.abstentions) lines.push(`${a.id}: ${s.abstentions[a.id]?.value ?? 'UNRESOLVED'}`)
  const q = quizScore(L, s)
  lines.push(`quiz: ${s.quizChecked ? `${q.right}/${q.total}` : 'not taken'}`)
  if (s.couldBreak.trim()) lines.push(`could_break: ${oneLine(s.couldBreak)}`)
  lines.push(`residual_risk: ${oneLine(s.risk) || 'none stated'}`)
  return lines.join('\n')
}

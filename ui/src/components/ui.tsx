import type { ReactNode } from 'react'
import { Check, Triangle, Diamond, Waves, Hand, CircleDashed } from 'lucide-react'
import type { Grade, Tier } from '../lib/ledger'

export const GRADE_META: Record<Grade, { label: string; color: string; Icon: typeof Check; border: string }> = {
  PROVEN: { label: 'checked by tool', color: 'var(--color-proven)', Icon: Check, border: 'solid' },
  MEASURED: { label: 'test result', color: 'var(--color-measured)', Icon: Triangle, border: 'solid' },
  HEURISTIC: { label: 'tool estimate', color: 'var(--color-heur)', Icon: Diamond, border: 'dashed' },
  ARGUED: { label: 'AI reasoning, unverified', color: 'var(--color-argued)', Icon: Waves, border: 'dotted' },
  ABSTAINED: { label: "AI won't decide", color: 'var(--color-abst)', Icon: Hand, border: 'double' },
  UNSUPPORTED: { label: 'not run', color: 'var(--color-unsup)', Icon: CircleDashed, border: 'dotted' },
}

export function GradeChip({ grade, short = false }: { grade: Grade; short?: boolean }) {
  const m = GRADE_META[grade]
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-card px-2 py-0.5 text-[11.5px] leading-5 whitespace-nowrap"
      style={{ border: `1.5px ${m.border} ${m.color}`, color: 'var(--color-ink)' }} title={m.label}>
      <m.Icon size={11} strokeWidth={2.5} style={{ color: m.color }} aria-hidden />
      {!short && m.label}
    </span>
  )
}

const TIER_META: Record<Tier, { shapes: string; word: string; hint: string }> = {
  LIGHT: { shapes: '◇', word: 'Light check', hint: 'behaviour proven unchanged' },
  STANDARD: { shapes: '◆', word: 'Normal review', hint: 'behaviour change with direct evidence' },
  DEEP: { shapes: '◆◆', word: 'Deep review', hint: 'policy, scope or contract change' },
}
export function TierBadge({ tier, big = false }: { tier: Tier; big?: boolean }) {
  const m = TIER_META[tier]
  return (
    <span className={`inline-flex items-center gap-2 rounded-lg border-2 border-ink bg-card font-semibold ${big ? 'px-3 py-1 text-lg' : 'px-2 py-0.5 text-sm'}`} title={m.hint}>
      <span aria-hidden className="tracking-tighter">{m.shapes}</span>{m.word}
    </span>
  )
}

export function Card({ children, className = '', tone = 'plain' }: { children: ReactNode; className?: string; tone?: 'plain' | 'risk' | 'accent' }) {
  const t = { plain: 'border-line', risk: 'border-risk/40 bg-risk-soft/40', accent: 'border-accent/30 bg-accent-soft/40' }[tone]
  return <div className={`rounded-2xl border bg-card p-5 shadow-[0_1px_0_rgba(0,0,0,0.03)] ${t} ${className}`}>{children}</div>
}

export function Label({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <div className={`label ${className}`}>{children}</div>
}

export function Btn({ children, onClick, kind = 'ghost', active = false, disabled = false, title }: {
  children: ReactNode; onClick?: () => void; kind?: 'primary' | 'ghost' | 'choice'; active?: boolean; disabled?: boolean; title?: string
}) {
  const base = 'inline-flex items-center gap-2 rounded-xl px-3.5 py-2 text-sm font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed'
  const k = kind === 'primary' ? 'bg-ink text-paper hover:bg-ink/85'
    : kind === 'choice' ? (active ? 'border-2 border-ink bg-ink text-paper' : 'border-2 border-line bg-card hover:border-ink/50')
    : 'border border-line bg-card hover:border-ink/40'
  return <button type="button" className={`${base} ${k}`} onClick={onClick} disabled={disabled} title={title} aria-pressed={kind === 'choice' ? active : undefined}>{children}</button>
}

export function SourceChip({ label, href }: { label: string; href: string | null }) {
  const cls = 'inline-flex items-center rounded-md border border-line bg-paper px-1.5 py-0.5 font-mono text-[11px] text-muted hover:text-ink'
  return href ? <a className={cls} href={href} target="_blank" rel="noopener noreferrer">{label}</a> : <span className={cls}>{label}</span>
}

/** Renders `backtick` spans as inline code; everything else as plain text (no HTML from data, ever). */
export function Rich({ text }: { text: string }) {
  const parts = String(text).split(/(`[^`]+`)/g)
  return <>{parts.map((p, i) => p.startsWith('`') && p.endsWith('`') && p.length > 2
    ? <code key={i} className="rounded bg-paper px-1 py-px font-mono text-[0.88em]">{p.slice(1, -1)}</code>
    : <span key={i}>{p}</span>)}</>
}

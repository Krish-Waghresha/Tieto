import { GRADE_META, GradeChip } from './ui'
import { GRADE_ORDER, type Grade } from '../lib/ledger'

/** Evidence ladder: strongest on the left, gaps on the right. Never a single percentage. */
export function TrustBar({ counts, onPick, active }: { counts: Record<string, number>; onPick?: (g: Grade | null) => void; active?: Grade | null }) {
  const items = GRADE_ORDER.map(g => ({ g, n: counts[g] ?? 0 })).filter(x => x.n > 0)
  const total = items.reduce((a, b) => a + b.n, 0) || 1
  return (
    <div>
      <div className="flex h-8 w-full overflow-hidden rounded-lg border border-line" role="img" aria-label="Evidence by grade, strongest first">
        {items.map(({ g, n }) => {
          const m = GRADE_META[g]
          const dim = active && active !== g
          return (
            <button key={g} type="button" onClick={() => onPick?.(active === g ? null : g)} title={`${m.label}: ${n}`}
              className={`flex items-center justify-center gap-1 text-xs font-semibold text-white transition-opacity ${g === 'UNSUPPORTED' ? 'hatch !text-ink' : ''} ${dim ? 'opacity-25' : ''}`}
              style={{ width: `${(100 * n) / total}%`, background: g === 'UNSUPPORTED' ? undefined : m.color }}>
              <m.Icon size={12} strokeWidth={3} aria-hidden />{n}
            </button>
          )
        })}
      </div>
      <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1.5">
        {items.map(({ g, n }) => <span key={g} className="inline-flex items-center gap-1 text-xs text-muted"><GradeChip grade={g} /> {n}</span>)}
      </div>
    </div>
  )
}

/** Two bars on one axis: what the requirement needs vs what the change touches. */
export function ScopeMeter({ needed, affected, grade }: { needed: number; affected: number; grade: Grade }) {
  const max = Math.max(needed, affected, 1)
  const row = (label: string, n: number, filled: boolean) => (
    <div className="flex items-center gap-3">
      <div className="w-24 shrink-0 text-right text-xs text-muted">{label}</div>
      <div className="h-5 flex-1 rounded bg-paper">
        <div className={`flex h-5 items-center justify-end rounded pr-2 text-xs font-semibold ${filled ? 'bg-ink text-paper' : 'border-2 border-risk text-risk'}`}
          style={{ width: `${Math.max(6, (100 * n) / max)}%` }}>{n}</div>
      </div>
    </div>
  )
  return (
    <div className="space-y-1.5">
      {row('fix needs', needed, true)}
      {row('change affects', affected, false)}
      <div className="flex items-center justify-between pl-27 text-xs text-muted">
        <span><b className="text-risk">{Math.round(affected / Math.max(needed, 1))}×</b> wider than the fix needs</span>
        <GradeChip grade={grade} />
      </div>
    </div>
  )
}

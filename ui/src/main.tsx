import { StrictMode, useCallback, useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { AnimatePresence, motion } from 'motion/react'
import { ArrowLeft, ArrowRight, BookOpen, Footprints } from 'lucide-react'
import './index.css'
import { ledger, emptyState, isDependent, proofCounts, unresolved, type Ledger, type ReviewState } from './lib/ledger'
import { STEPS } from './steps/Steps'
import { TierBadge } from './components/ui'

// Record CSP violations on <body data-csp> so automated checks (headless Chrome --dump-dom) can assert zero.
const violations: string[] = []
document.addEventListener('securitypolicyviolation', e => {
  violations.push(`${e.violatedDirective}:${(e.sample || '').slice(0, 40)}`)
  document.body.dataset.csp = violations.join(' | ')
})
const stepFromHash = () => { const n = parseInt(location.hash.replace(/^#step-?/, ''), 10); return Number.isFinite(n) ? n - 1 : 0 }

const KEY = (L: Ledger) => `dfr:${L.pin.head}:${L.ledger_sha256.slice(0, 12)}`

function stepDone(L: Ledger, s: ReviewState, key: string): boolean {
  if (key === 'decisions') return L.decisions.filter(d => !isDependent(d)).every(d => s.decisions[d.id])
  if (key === 'findings') return L.findings.every(f => s.findings[f.id]) && L.abstentions.every(a => s.abstentions[a.id])
  if (key === 'quiz') return s.quizChecked
  if (key === 'sign') return unresolved(L, s).length === 0
  return false
}

function App({ L }: { L: Ledger }) {
  const [s, setS] = useState<ReviewState>(() => {
    try { return { ...emptyState(), ...JSON.parse(localStorage.getItem(KEY(L)) ?? '{}') } } catch { return emptyState() }
  })
  const [i, setI] = useState(() => Math.max(0, Math.min(STEPS.length - 1, stepFromHash())))
  const [full, setFull] = useState(false)
  const set = useCallback((f: (s: ReviewState) => ReviewState) => setS(prev => f(prev)), [])
  const go = useCallback((n: number) => {
    const k = Math.max(0, Math.min(STEPS.length - 1, n))
    setI(k); history.replaceState(null, '', `#step-${k + 1}`); window.scrollTo({ top: 0, behavior: 'smooth' })
  }, [])
  useEffect(() => { const f = () => setI(Math.max(0, Math.min(STEPS.length - 1, stepFromHash()))); window.addEventListener('hashchange', f); return () => window.removeEventListener('hashchange', f) }, [])
  useEffect(() => { try { localStorage.setItem(KEY(L), JSON.stringify(s)) } catch { /* file:// may block storage */ } }, [L, s])
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (full || (e.target as HTMLElement)?.closest('textarea,input')) return
      if (e.key === 'ArrowRight') go(i + 1)
      if (e.key === 'ArrowLeft') go(i - 1)
    }
    window.addEventListener('keydown', onKey); return () => window.removeEventListener('keydown', onKey)
  }, [i, full, go])
  const pc = proofCounts(L)
  const Step = STEPS[i].C
  return (
    <div className="min-h-screen">
      <header className="sticky top-0 z-20 border-b border-line bg-paper/90 backdrop-blur">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-4 gap-y-2 px-5 py-3">
          <div className="flex items-center gap-2">
            <span className="flex size-7 items-center justify-center rounded-lg bg-ink font-mono text-xs font-bold text-paper">DF</span>
            <div className="leading-tight"><div className="text-sm font-semibold">Decision-First Review</div>
              <div className="font-mono text-[11px] text-muted">{L.requirement.id} · PR #{L.pin.pr} · {L.pin.head.slice(0, 7)}</div></div>
          </div>
          <TierBadge tier={L.triage.tier} />
          <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${pc.ran ? 'bg-accent-soft' : 'hatch border border-line'}`}><span className="rounded bg-paper/90 px-1">checks run {pc.ran}/{pc.total}</span></span>
          <div className="ml-auto inline-flex rounded-xl border border-line bg-card p-0.5 text-sm">
            <button type="button" onClick={() => setFull(false)} className={`flex items-center gap-1.5 rounded-lg px-3 py-1 ${!full ? 'bg-ink text-paper' : 'text-muted'}`}><Footprints size={14} />Guided</button>
            <button type="button" onClick={() => setFull(true)} className={`flex items-center gap-1.5 rounded-lg px-3 py-1 ${full ? 'bg-ink text-paper' : 'text-muted'}`}><BookOpen size={14} />Full page</button>
          </div>
        </div>
        {!full && (
          <nav className="mx-auto flex max-w-6xl gap-1 overflow-x-auto px-5 pb-2" aria-label="Review steps">
            {STEPS.map((st, k) => {
              const done = stepDone(L, s, st.key)
              return (
                <button key={st.key} type="button" onClick={() => go(k)} aria-current={k === i ? 'step' : undefined}
                  className={`group flex min-w-[118px] flex-1 flex-col items-start gap-1 rounded-lg px-2 py-1.5 text-left ${k === i ? 'bg-card shadow-sm' : 'hover:bg-card/60'}`}>
                  <span className={`h-1 w-full rounded-full ${k === i ? 'bg-accent' : done || k < i ? 'bg-ink/70' : 'bg-line'}`} />
                  <span className={`text-xs ${k === i ? 'font-semibold' : 'text-muted'}`}><span className="font-mono">{k + 1}</span> {st.label}{done ? ' ✓' : ''}</span>
                </button>
              )
            })}
          </nav>
        )}
      </header>

      <main className="mx-auto max-w-6xl px-5 py-8">
        {full ? (
          <div className="space-y-14">{STEPS.map(st => <section key={st.key}><st.C L={L} s={s} set={set} go={go} /></section>)}</div>
        ) : (
          <AnimatePresence mode="wait">
            <motion.section key={i} initial={{ opacity: 0, x: 24 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -24 }} transition={{ duration: 0.22 }}>
              <Step L={L} s={s} set={set} go={go} />
            </motion.section>
          </AnimatePresence>
        )}
        {!full && (
          <div className="mt-10 flex items-center justify-between border-t border-line pt-5">
            <button type="button" disabled={i === 0} onClick={() => go(i - 1)} className="flex items-center gap-2 text-sm text-muted disabled:opacity-30"><ArrowLeft size={16} />{i > 0 ? STEPS[i - 1].label : 'Back'}</button>
            <span className="font-mono text-xs text-muted">← → to move · step {i + 1} of {STEPS.length}</span>
            <button type="button" disabled={i === STEPS.length - 1} onClick={() => go(i + 1)} className="flex items-center gap-2 text-sm font-semibold disabled:opacity-30">{i < STEPS.length - 1 ? STEPS[i + 1].label : 'Done'}<ArrowRight size={16} /></button>
          </div>
        )}
        <footer className="mt-10 text-xs text-muted">{L.status_note} · record <span className="font-mono">{L.ledger_sha256.slice(0, 12)}</span></footer>
      </main>
    </div>
  )
}

const root = createRoot(document.getElementById('root')!)
if (!ledger) {
  root.render(<div className="p-10 font-mono text-sm">No review record injected. Build with the reviewbot (python -m reviewbot review …).</div>)
} else {
  root.render(<StrictMode><App L={ledger} /></StrictMode>)
}

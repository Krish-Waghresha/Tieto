import { useState } from 'react'
import { motion, AnimatePresence } from 'motion/react'
import { Lock, Unlock, ArrowRight, CornerDownRight, FlaskConical, Wrench } from 'lucide-react'
import { Btn, Card, GradeChip, Label, Rich, SourceChip } from './ui'
import { CodeExcerpt } from './Code'
import { hunkLabel, isDependent, parentOf, sourceUrl, type Abstention, type AbstPick, type Decision, type DecisionPick, type Finding, type FindingPick, type Ledger } from '../lib/ledger'

const REC_WORD: Record<string, string> = { accept: 'Accept as is', request_change: 'Request a change', reject: 'Reject' }

function Sources({ L, ids }: { L: Ledger; ids: string[] }) {
  return <div className="flex flex-wrap gap-1.5">{ids.map(id => <SourceChip key={id} label={hunkLabel(id)} href={sourceUrl(L, id)} />)}</div>
}

function proofLine(p: { id: string; status: string; result: string }) {
  const ran = p.status === 'executed'
  return <span key={p.id} className="inline-flex items-center gap-1"><b className="font-mono text-xs">{p.id}</b><GradeChip grade={ran ? 'MEASURED' : 'UNSUPPORTED'} />{ran && <span className="text-xs">{p.result}</span>}</span>
}

export function DecisionCard({ L, d, pick, onPick, showCode = true }: { L: Ledger; d: Decision; pick?: DecisionPick; onPick: (p: DecisionPick) => void; showCode?: boolean }) {
  const [more, setMore] = useState(false)
  if (isDependent(d)) {
    return (
      <Card className="!py-3.5">
        <div className="flex items-start gap-3">
          <CornerDownRight size={18} className="mt-0.5 text-muted" aria-hidden />
          <div className="flex-1">
            <div className="flex flex-wrap items-center gap-2"><b className="font-mono text-xs">{d.id}</b><span className="font-semibold"><Rich text={d.title} /></span></div>
            <p className="mt-1 text-sm text-muted">Follows <b>{parentOf(d)}</b> — no separate verdict. {d.recommendation_reason}</p>
            <div className="mt-2"><Sources L={L} ids={d.claims} /></div>
          </div>
        </div>
      </Card>
    )
  }
  const snip = L.snippets[d.claims[0]]
  const options: DecisionPick[] = [
    { value: 'accept' },
    ...d.alternatives.map(a => ({ value: 'request_change' as const, prefer: a })),
    { value: 'reject' },
  ]
  const same = (a?: DecisionPick, b?: DecisionPick) => !!a && !!b && a.value === b.value && (a.prefer ?? '') === (b.prefer ?? '')
  const agrees = pick && pick.value === d.recommended
  return (
    <Card>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2"><b className="rounded-md bg-ink px-1.5 py-0.5 font-mono text-xs text-paper">{d.id}</b><h3 className="text-lg font-semibold"><Rich text={d.title} /></h3></div>
        <GradeChip grade="ARGUED" />
      </div>
      <div className="mt-1 text-sm text-muted">Requirement: <b className={d.trace.status === 'traced' ? 'text-measured' : 'text-risk'}>{d.trace.status}</b>{d.trace.to.length > 0 && <> → {d.trace.to.join(', ')}</>} · Why (agent): {d.rationale}</div>

      <div className="mt-4 grid gap-3 md:grid-cols-2">
        <div className="rounded-xl border border-line bg-paper/60 p-3.5"><Label>Before</Label><p className="mt-1.5 text-[15px]"><Rich text={d.before} /></p></div>
        <div className="rounded-xl border-2 border-dashed border-argued/70 bg-card p-3.5"><Label>After</Label><p className="mt-1.5 text-[15px]"><Rich text={d.after} /></p></div>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2 text-sm">
        <Sources L={L} ids={d.claims} />
        {d.evidence.length > 0 && <span className="flex flex-wrap items-center gap-2 text-muted">checks: {d.evidence.map(proofLine)}</span>}
        <button type="button" className="text-sm text-accent underline-offset-2 hover:underline" onClick={() => setMore(!more)}>{more ? 'hide' : 'show'} code & risk</button>
      </div>

      <AnimatePresence>{more && (
        <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} className="overflow-hidden">
          <div className="mt-3 grid gap-3 md:grid-cols-2">
            {Object.entries(d.dimensions).map(([k, v]) => <div key={k} className="text-sm"><Label>{k.replace('_', ' ')}</Label><div>{v}</div></div>)}
          </div>
          {showCode && snip && (
            <div className="mt-3 grid gap-3 lg:grid-cols-2">
              {snip.before && !snip.before.insertion && <CodeExcerpt ex={snip.before} lang={snip.lang} tone="before" title={`before · ${hunkLabel(d.claims[0])}`} maxLines={10} />}
              {snip.after && <CodeExcerpt ex={snip.after} lang={snip.lang} tone="after" title={`after · ${hunkLabel(d.claims[0])}`} maxLines={10} />}
            </div>
          )}
        </motion.div>)}
      </AnimatePresence>

      <div className="mt-4 border-t border-line pt-4">
        <Label>Your verdict first</Label>
        <div className="mt-2 flex flex-wrap gap-2">
          {options.map((o, i) => (
            <Btn key={i} kind="choice" active={same(pick, o)} onClick={() => onPick(o)}>
              {o.value === 'accept' ? 'Accept as is' : o.value === 'reject' ? 'Reject' : <>Change: <Rich text={o.prefer ?? ''} /></>}
            </Btn>
          ))}
        </div>
        <div className="mt-3">
          {!pick ? (
            <div className="flex items-center gap-2 text-sm text-muted"><Lock size={14} aria-hidden /> The AI's recommendation unlocks after you choose.</div>
          ) : (
            <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className={`flex items-start gap-2 rounded-xl p-3 text-sm ${agrees ? 'bg-accent-soft' : 'bg-[#fff6e0]'}`}>
              <Unlock size={15} className="mt-0.5 shrink-0" aria-hidden />
              <div><b>AI suggests: {REC_WORD[d.recommended] ?? d.recommended}</b> — {d.recommendation_reason}
                <span className="ml-1 font-semibold">{agrees ? '· you agree' : '· you differ — that is fine, you own the call'}</span></div>
            </motion.div>
          )}
        </div>
      </div>
    </Card>
  )
}

export function FindingCard({ L, f, pick, onPick }: { L: Ledger; f: Finding; pick?: FindingPick; onPick: (p: FindingPick) => void }) {
  const facts = L.facts.filter(x => f.facts.includes(x.id))
  const ran = f.evidence.some(p => p.status === 'executed')
  const status = { CONFIRMED: 'confirmed by a test', DISPROVED: 'disproved by a test', 'NOT CONFIRMED': 'test did not confirm it' }[f.status] ?? 'not yet tested'
  return (
    <Card tone="risk">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2"><b className="rounded-md bg-risk px-1.5 py-0.5 font-mono text-xs text-white">{f.id}</b><h3 className="text-lg font-semibold">AI finding: <Rich text={f.title} /></h3></div>
        <GradeChip grade={f.grade} />
      </div>
      <p className="mt-2 text-[15px]"><Rich text={f.argument} /></p>
      <div className="mt-3 grid gap-3 md:grid-cols-2">
        <div><Label>Tool facts behind it</Label>
          <ul className="mt-1.5 space-y-1.5 text-sm">{facts.map(x => <li key={x.id} className="flex gap-2"><span>{x.holds ? '✔' : '✕'}</span><span><Rich text={x.text} /> <GradeChip grade={x.grade} short /></span></li>)}</ul></div>
        <div><Label>Tests that try to disprove it</Label>
          <ul className="mt-1.5 space-y-1.5 text-sm">{f.evidence.map(p => <li key={p.id} className="flex flex-wrap items-center gap-2"><FlaskConical size={14} aria-hidden />{p.title} {proofLine(p)}</li>)}</ul>
          <p className="mt-2 text-sm"><b>Status:</b> {status}{!ran && ' — the probe is defined but has not run in this environment.'}</p></div>
      </div>
      <p className="mt-3 flex items-start gap-2 text-sm text-muted"><Wrench size={14} className="mt-0.5" aria-hidden /> <Rich text={f.fix_hint} /></p>
      <div className="mt-3"><Sources L={L} ids={f.claims} /></div>
      <div className="mt-4 flex flex-wrap gap-2 border-t border-risk/20 pt-4">
        <Btn kind="choice" active={pick?.value === 'valid' && !pick.note} onClick={() => onPick({ value: 'valid' })}>Looks real</Btn>
        <Btn kind="choice" active={pick?.value === 'invalid'} onClick={() => onPick({ value: 'invalid' })}>Not an issue</Btn>
        <Btn kind="choice" active={!!pick?.note} onClick={() => onPick({ value: 'valid', note: 'unconfirmed — test requested before merge' })}>Unsure — ask for a test <ArrowRight size={14} /></Btn>
      </div>
    </Card>
  )
}

export function AbstentionCard({ a, pick, onPick }: { a: Abstention; pick?: AbstPick; onPick: (p: AbstPick) => void }) {
  const wont = a.grade === 'ABSTAINED'
  return (
    <Card>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2"><b className="rounded-md border-2 border-double border-abst px-1.5 py-0.5 font-mono text-xs">{a.id}</b>
          <h3 className="font-semibold">{wont ? "AI won't decide: " : 'Not checked: '}<Rich text={a.title} /></h3></div>
        <GradeChip grade={a.grade} />
      </div>
      <p className="mt-2 text-sm"><b>Why:</b> <Rich text={a.why} /></p>
      <p className="mt-1 text-sm"><b>Your call:</b> {a.human_action}</p>
      <div className="mt-3 flex flex-wrap gap-2">
        <Btn kind="choice" active={pick?.value === 'resolved'} onClick={() => onPick({ value: 'resolved' })}>Resolved</Btn>
        <Btn kind="choice" active={pick?.value === 'accept_risk'} onClick={() => onPick({ value: 'accept_risk' })}>Accept as residual risk</Btn>
        <Btn kind="choice" active={pick?.value === 'defer'} onClick={() => onPick({ value: 'defer' })}>Defer to owner / maintainers</Btn>
      </div>
    </Card>
  )
}

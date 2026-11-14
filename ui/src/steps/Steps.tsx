import { useState } from 'react'
import { motion } from 'motion/react'
import { ArrowRight, Copy, Check, AlertTriangle, ShieldCheck, Users, CircleDashed } from 'lucide-react'
import { Btn, Card, GradeChip, Label, Rich, SourceChip, TierBadge } from '../components/ui'
import { ScopeMeter, TrustBar } from '../components/viz'
import { FlowGraph, useFlow, type GraphMode } from '../components/FlowGraph'
import { CodeExcerpt } from '../components/Code'
import { AbstentionCard, DecisionCard, FindingCard } from '../components/Cards'
import { AudioBrief } from '../components/Audio'
import {
  audio, hunkLabel, isDependent, orderedDecisions, proofCounts, quizScore, signText, sourceUrl, suggestedFinal, unresolved,
  type Grade, type Ledger, type ReviewState,
} from '../lib/ledger'

export type StepProps = { L: Ledger; s: ReviewState; set: (f: (s: ReviewState) => ReviewState) => void; go: (i: number) => void }

const owner = (L: Ledger) => L.owners?.[0]?.owner ?? 'a named area owner'

function H({ kicker, title, sub }: { kicker: string; title: string; sub?: string }) {
  return <header className="mb-5"><Label>{kicker}</Label><h2 className="mt-1 text-[28px] font-semibold leading-tight tracking-tight">{title}</h2>{sub && <p className="mt-1.5 max-w-3xl text-muted">{sub}</p>}</header>
}

// 1 ─ Verdict & who decides
export function StepVerdict({ L, go }: StepProps) {
  const pc = proofCounts(L)
  const sc = L.scope.find(x => x.mismatch)
  return (
    <div>
      <H kicker="Step 1 · Verdict" title="How careful do you need to be — and is it your call?" />
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1.4fr)_minmax(0,1fr)]">
        <Card>
          <div className="flex flex-wrap items-center gap-3"><TierBadge tier={L.triage.tier} big /><span className="text-sm text-muted">set by plain code from the policy — AI cannot lower it</span></div>
          {L.summary && <>
            <p className="mt-4 text-[17px] leading-relaxed">{L.summary.what}</p>
            <div className="mt-4 rounded-xl border-l-4 border-heur bg-[#fff8e8] p-3.5 text-[15px]"><Label>Bot's read</Label><p className="mt-1">{L.summary.verdict}</p></div>
          </>}
          <div className="mt-4 flex items-center gap-2 text-[15px]"><Users size={16} aria-hidden />Decides: <b className="font-mono">{owner(L)}</b><span className="text-muted">— not the PR author, not the AI</span></div>
        </Card>
        <div className="space-y-4">
          <Card tone={pc.ran ? 'plain' : 'risk'}>
            <Label>Checks actually run</Label>
            <div className="mt-1 flex items-baseline gap-2"><span className="text-4xl font-semibold">{pc.ran}</span><span className="text-muted">of {pc.total}</span></div>
            <p className="mt-1 text-sm">{pc.ran ? (pc.violated.length ? `Violated: ${pc.violated.join(', ')}` : 'None violated.') : 'Nothing executed yet — what follows is tool facts and AI reasoning.'}</p>
          </Card>
          {sc && <Card><Label>Scope check</Label><div className="mt-3"><ScopeMeter needed={sc.requirement_sites} affected={sc.reach} grade={sc.grade} /></div></Card>}
        </div>
      </div>
      <Card className="mt-4"><Label className="mb-2">Evidence, strongest first</Label><TrustBar counts={L.grade_counts} /></Card>
      <div className="mt-4 grid gap-4 lg:grid-cols-[1fr_auto] lg:items-center">
        <AudioBrief audio={audio} />
        <Btn kind="primary" onClick={() => go(1)}>Start review <ArrowRight size={16} /></Btn>
      </div>
    </div>
  )
}

// 2 ─ What changed
export function StepChange({ L }: StepProps) {
  const [mode, setMode] = useState<GraphMode>('after')
  const flow = useFlow(L)
  const [sel, setSel] = useState<string | null>(flow?.br ? `method:${flow.br.method}` : flow?.fanHunk ?? null)
  const snip = sel && sel !== 'callers' ? L.snippets[sel] : null
  const selLabel = sel?.startsWith('method:') ? `${sel.slice(7)}()` : sel ? hunkLabel(sel) : ''
  const fan = flow?.fan
  const byMethod = fan?.sites?.reduce<Record<string, number[]>>((a, x) => ((a[x.method] ??= []).push(x.line), a), {}) ?? {}
  return (
    <div>
      <H kicker="Step 2 · What changed" title="What does the system do differently now?" sub="Toggle before and after. Only the change moves. Click a box to see its code." />
      <div className="mb-3 inline-flex rounded-xl border border-line bg-card p-1" role="tablist">
        {(['before', 'after'] as GraphMode[]).map(m => (
          <button key={m} type="button" role="tab" aria-selected={mode === m} onClick={() => setMode(m)}
            className={`rounded-lg px-4 py-1.5 text-sm font-semibold capitalize ${mode === m ? 'bg-ink text-paper' : 'text-muted'}`}>{m}</button>
        ))}
      </div>
      <FlowGraph L={L} mode={mode} selected={sel} onSelect={setSel} />
      <p className="mt-3 text-[17px]">
        {mode === 'before'
          ? <>Before: every one of the <b>{fan?.count}</b> call sites reports its warning straight to the user.</>
          : <>After: all <b>{fan?.count}</b> call sites pass through a new filter. A warning without a location in this project is <b className="text-risk">dropped silently</b>.</>}
        <span className="ml-2 align-middle"><GradeChip grade="HEURISTIC" /></span>
      </p>
      <div className="mt-4">
        {sel === 'callers' && fan ? (
          <Card><Label>Where the {fan.count} call sites are</Label>
            <ul className="mt-2 grid gap-2 sm:grid-cols-3">{Object.entries(byMethod).map(([m, lines]) => (
              <li key={m} className="rounded-xl border border-line p-3"><div className="font-mono text-sm font-semibold">{m}</div><div className="text-sm text-muted">{lines.length} sites · lines {lines.slice(0, 6).join(', ')}{lines.length > 6 ? '…' : ''}</div></li>))}</ul>
          </Card>
        ) : snip ? (
          <div className="grid gap-3 lg:grid-cols-2">
            {snip.before && !snip.before.insertion
              ? <CodeExcerpt ex={snip.before} lang={snip.lang} tone="before" title={`before · ${selLabel}`} maxLines={14} />
              : <div className="flex items-center justify-center rounded-xl border border-dashed border-line bg-card p-6 text-sm text-muted">Before: nothing here — this is new code.</div>}
            {snip.after && <CodeExcerpt ex={snip.after} lang={snip.lang} tone="after" title={`after · ${selLabel}`} maxLines={14} />}
          </div>
        ) : null}
      </div>
    </div>
  )
}

// 3 ─ Decisions
export function StepDecisions({ L, s, set }: StepProps) {
  const ds = orderedDecisions(L)
  const done = ds.filter(d => !isDependent(d) && s.decisions[d.id]).length
  const total = ds.filter(d => !isDependent(d)).length
  return (
    <div>
      <H kicker={`Step 3 · Decisions · ${done} of ${total} decided`} title="Do you agree with each choice the agent made?" sub="Pick first. The AI's suggestion unlocks after — people over-trust AI explanations when they see them first." />
      <div className="space-y-4">{ds.map(d => <DecisionCard key={d.id} L={L} d={d} pick={s.decisions[d.id]} onPick={p => set(x => ({ ...x, decisions: { ...x.decisions, [d.id]: p } }))} />)}</div>
    </div>
  )
}

// 4 ─ Found / won't decide
export function StepFindings({ L, s, set }: StepProps) {
  return (
    <div>
      <H kicker="Step 4 · What the AI found — and won't decide" title="Is the finding real? What is left to you?" />
      <div className="space-y-4">
        {L.findings.map(f => <FindingCard key={f.id} L={L} f={f} pick={s.findings[f.id]} onPick={p => set(x => ({ ...x, findings: { ...x.findings, [f.id]: p } }))} />)}
        {L.abstentions.map(a => <AbstentionCard key={a.id} a={a} pick={s.abstentions[a.id]} onPick={p => set(x => ({ ...x, abstentions: { ...x.abstentions, [a.id]: p } }))} />)}
      </div>
    </div>
  )
}

// 5 ─ Evidence & gaps
export function StepEvidence({ L }: StepProps) {
  const [g, setG] = useState<Grade | null>(null)
  const facts = L.facts.filter(f => !g || f.grade === g)
  const proofs = L.proofs.filter(p => !g || (p.status === 'executed' ? p.grade : 'UNSUPPORTED') === g)
  return (
    <div>
      <H kicker="Step 5 · Evidence & gaps" title="What was actually checked — and what was not?" sub="Click a segment to filter. Gaps are never hidden." />
      <Card><TrustBar counts={L.grade_counts} onPick={setG} active={g} /></Card>
      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <Card>
          <Label>Checks (executed tests)</Label>
          <ul className="mt-2 divide-y divide-line">{proofs.map(p => (
            <li key={p.id} className="flex items-start gap-3 py-2.5">
              <b className="w-9 shrink-0 font-mono text-xs">{p.id}</b>
              <div className="flex-1 text-sm">{p.title}<div className="text-xs text-muted">{p.note}</div></div>
              {p.status === 'executed' ? <GradeChip grade="MEASURED" /> : <GradeChip grade="UNSUPPORTED" />}
            </li>))}</ul>
        </Card>
        <Card>
          <Label>Tool facts</Label>
          <ul className="mt-2 divide-y divide-line">{facts.map(f => (
            <li key={f.id} className="flex items-start gap-3 py-2.5 text-sm">
              <span className="w-4 shrink-0">{f.holds === false ? '✕' : f.holds ? '✔' : '·'}</span>
              <div className="flex-1"><Rich text={f.text} /></div><GradeChip grade={f.grade} short />
            </li>))}</ul>
        </Card>
      </div>
      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <Card>
          <Label>Every changed block is explained by…</Label>
          <ul className="mt-2 space-y-1.5">{L.coverage.hunks.map(h => (
            <li key={h.id} className="flex items-center gap-2 text-sm">
              <SourceChip label={hunkLabel(h.id)} href={sourceUrl(L, h.id)} />
              <span className="text-xs text-muted">+{h.added}/−{h.removed}</span>
              <span className="ml-auto flex gap-1">{h.claimed_by.length ? h.claimed_by.map(c => <b key={c} className="rounded bg-paper px-1.5 font-mono text-[11px]">{c}</b>) : <b className="text-risk">nothing</b>}</span>
            </li>))}</ul>
          <p className="mt-2 text-xs text-muted">{L.coverage.complete ? 'All blocks assigned (assignment by the simulated extractor).' : 'Unexplained blocks raise the tier.'}</p>
        </Card>
        <Card tone="risk">
          <Label>Not checked</Label>
          <ul className="mt-2 space-y-1.5 text-sm">{L.not_checked.map(n => <li key={n} className="flex gap-2"><CircleDashed size={14} className="mt-0.5 shrink-0 text-unsup" aria-hidden />{n}</li>)}</ul>
          <Label className="mt-4">Why this tier</Label>
          <ul className="mt-2 space-y-2 text-sm">{L.triage.fired.filter(f => f.tier).map(f => (
            <li key={f.rule}><b className="font-mono text-xs">{f.rule}</b> <Rich text={f.detail} /><div className="text-xs text-muted">{f.motivated_by}</div></li>))}</ul>
        </Card>
      </div>
    </div>
  )
}

// 6 ─ Quick check
export function StepQuiz({ L, s, set, go }: StepProps) {
  const qs = L.quiz.filter(q => q.kind !== 'free')
  const free = L.quiz.find(q => q.kind === 'free')
  const [i, setI] = useState(0)
  const q = qs[i]
  const answered = q ? s.quiz[q.id] !== undefined : false
  const score = quizScore(L, s)
  return (
    <div>
      <H kicker="Step 6 · Quick check (optional)" title="Check your read" sub="Three questions on consequences. Answer keys come from tool facts or tests, never from the AI. Never blocks sign-off." />
      <div className="mb-4 flex gap-1.5">{qs.map((x, k) => <span key={x.id} className={`h-1.5 w-10 rounded-full ${k < i || (k === i && answered) ? 'bg-ink' : 'bg-line'}`} />)}</div>
      {q && !s.quizChecked && (
        <Card>
          <div className="flex items-center justify-between"><Label>Question {i + 1} of {qs.length}</Label>{q.key_grade && <span className="text-xs text-muted">key: <GradeChip grade={q.key_grade} /></span>}</div>
          <h3 className="mt-2 text-xl font-semibold">{q.question}</h3>
          <div className="mt-4 grid gap-2">{q.options?.map((o, k) => {
            const chosen = s.quiz[q.id] === k
            const right = answered && k === q.answer
            const wrong = answered && chosen && k !== q.answer
            return (
              <button key={k} type="button" disabled={answered} onClick={() => set(x => ({ ...x, quiz: { ...x.quiz, [q.id]: k } }))}
                className={`rounded-xl border-2 px-4 py-3 text-left text-[15px] transition-colors ${right ? 'border-measured bg-[#eef8f4]' : wrong ? 'border-risk bg-risk-soft' : chosen ? 'border-ink' : 'border-line bg-card hover:border-ink/40'}`}>
                {q.kind === 'line' ? <span className="font-mono text-sm">{hunkLabel(o)}</span> : o}
                {right && <Check size={16} className="float-right text-measured" />}
              </button>)
          })}</div>
          {answered && <p className="mt-3 text-sm text-muted">{q.explain}</p>}
          <div className="mt-4 flex justify-between">
            <Btn onClick={() => set(x => ({ ...x, quizChecked: true }))}>Skip</Btn>
            <Btn kind="primary" disabled={!answered} onClick={() => (i + 1 < qs.length ? setI(i + 1) : set(x => ({ ...x, quizChecked: true })))}>{i + 1 < qs.length ? 'Next question' : 'Finish'} <ArrowRight size={16} /></Btn>
          </div>
        </Card>
      )}
      {s.quizChecked && (
        <Card>
          <div className="text-xl font-semibold">{score.right} of {score.total} — recorded in your sign-off, never a gate.</div>
          {free && <div className="mt-4"><Label>{free.question}</Label>
            <textarea className="mt-2 w-full rounded-xl border border-line bg-paper p-3" rows={2} maxLength={400} value={s.couldBreak}
              onChange={e => set(x => ({ ...x, couldBreak: e.target.value }))} placeholder="e.g. positional records stop warning about null keys" /></div>}
          <div className="mt-3 flex gap-2"><Btn onClick={() => { setI(0); set(x => ({ ...x, quiz: {}, quizChecked: false })) }}>Retry</Btn><Btn kind="primary" onClick={() => go(6)}>Continue to sign <ArrowRight size={16} /></Btn></div>
        </Card>
      )}
    </div>
  )
}

// 7 ─ Sign
export function StepSign({ L, s, set }: StepProps) {
  const [copied, setCopied] = useState(false)
  const open = unresolved(L, s)
  const final = s.final ?? suggestedFinal(L, s)
  const txt = signText(L, s)
  const pc = proofCounts(L)
  const rows = [
    ...L.decisions.filter(d => !isDependent(d)).map(d => ({ id: d.id, title: d.title, you: s.decisions[d.id] ? (s.decisions[d.id].value === 'accept' ? 'accept' : s.decisions[d.id].value === 'reject' ? 'reject' : `change: ${s.decisions[d.id].prefer}`) : null, ai: d.recommended })),
    ...L.findings.map(f => ({ id: f.id, title: f.title, you: s.findings[f.id] ? (s.findings[f.id].note ? 'ask for a test' : s.findings[f.id].value) : null, ai: '—' })),
    ...L.abstentions.map(a => ({ id: a.id, title: a.title, you: s.abstentions[a.id]?.value ?? null, ai: 'won\'t decide' })),
  ]
  return (
    <div>
      <H kicker="Step 7 · Sign" title="What exactly are you signing?" sub="Your choices become a /sign review. The bot checks the commit, every item, the review state, and that you are not the PR author." />
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1.25fr)_minmax(0,1fr)]">
        <Card>
          <Label>You vs AI</Label>
          <ul className="mt-2 divide-y divide-line">{rows.map(r => (
            <li key={r.id} className="flex items-center gap-3 py-2.5 text-sm">
              <b className="w-8 font-mono text-xs">{r.id}</b><span className="flex-1 truncate"><Rich text={r.title} /></span>
              <span className={`rounded-md px-2 py-0.5 text-xs font-semibold ${r.you ? 'bg-ink text-paper' : 'border border-dashed border-risk text-risk'}`}>{r.you ?? 'open'}</span>
              <span className="w-32 text-right text-xs text-muted">AI: {({ accept: 'accept', request_change: 'request a change', reject: 'reject', follow_D1: 'follows D1' } as Record<string, string>)[r.ai] ?? r.ai}</span>
            </li>))}</ul>
          <div className="mt-3 flex items-start gap-2 rounded-xl bg-paper p-3 text-sm"><AlertTriangle size={15} className="mt-0.5 shrink-0 text-heur" />
            <span>Still open: {pc.total - pc.ran} of {pc.total} checks have not run. You sign what was checked <i>and</i> what was not.</span></div>
          <label className="mt-4 block"><Label>Residual risk you accept</Label>
            <textarea className="mt-2 w-full rounded-xl border border-line bg-paper p-3 text-sm" rows={2} maxLength={500} value={s.risk}
              onChange={e => set(x => ({ ...x, risk: e.target.value }))} placeholder="e.g. none — requesting changes" /></label>
        </Card>
        <Card>
          <Label>Decision</Label>
          <div className="mt-2 flex flex-wrap gap-2">
            {(['request_changes', 'approve', 'reject'] as const).map(v => (
              <Btn key={v} kind="choice" active={final === v} onClick={() => set(x => ({ ...x, final: v }))}>{v.replace('_', ' ')}</Btn>))}
          </div>
          {final === 'approve' && suggestedFinal(L, s) !== 'approve' && <p className="mt-2 text-sm text-risk">You requested changes on some items — the bot will reject an approval that contradicts them.</p>}
          <Label className="mt-4">Your /sign text</Label>
          <pre className="mt-2 max-h-64 overflow-auto whitespace-pre-wrap break-all rounded-xl bg-ink p-3 font-mono text-[12px] leading-relaxed text-paper">{txt}</pre>
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <Btn kind="primary" disabled={open.length > 0} title={open.length ? `Resolve ${open.join(', ')} first` : ''}
              onClick={() => { navigator.clipboard?.writeText(txt); setCopied(true); setTimeout(() => setCopied(false), 1800) }}>
              {copied ? <Check size={16} /> : <Copy size={16} />}{copied ? 'Copied' : 'Copy /sign text'}</Btn>
            {open.length > 0 && <span className="text-sm text-risk">Resolve {open.join(', ')} first</span>}
          </div>
          <ol className="mt-4 list-decimal space-y-1 pl-5 text-sm text-muted">
            <li>On the PR: <b>Files changed → Review changes</b></li>
            <li>Paste the text, choose <b>{final === 'approve' ? 'Approve' : 'Request changes'}</b>, submit</li>
            <li>The bot records it and sets the <code>decision-record</code> check</li>
          </ol>
          <p className="mt-3 flex items-center gap-1.5 text-xs text-muted"><ShieldCheck size={13} /> The AI never signs and never counts as a reviewer.</p>
        </Card>
      </div>
    </div>
  )
}

export const STEPS = [
  { key: 'verdict', label: 'Verdict', C: StepVerdict },
  { key: 'change', label: 'What changed', C: StepChange },
  { key: 'decisions', label: 'Decisions', C: StepDecisions },
  { key: 'findings', label: 'Found / won\'t decide', C: StepFindings },
  { key: 'evidence', label: 'Evidence & gaps', C: StepEvidence },
  { key: 'quiz', label: 'Quick check', C: StepQuiz },
  { key: 'sign', label: 'Sign', C: StepSign },
]
export const StepMotion = motion.div

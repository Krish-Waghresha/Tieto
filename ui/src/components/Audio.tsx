import { useEffect, useRef, useState } from 'react'
import { Play, Pause, Square } from 'lucide-react'
import type { AudioPayload } from '../lib/ledger'

/** ≤60 s briefing of the WHY. Pre-generated clip if embedded, else the browser's speech engine. Never autoplays. */
export function AudioBrief({ audio }: { audio: AudioPayload }) {
  const el = useRef<HTMLAudioElement>(null)
  const [playing, setPlaying] = useState(false)
  const [t, setT] = useState(0)
  const [dur, setDur] = useState(0)
  const [open, setOpen] = useState(false)
  useEffect(() => () => { window.speechSynthesis?.cancel() }, [])
  if (!audio.script && !audio.src) return null
  const toggle = () => {
    if (audio.src && el.current) { playing ? el.current.pause() : el.current.play(); return }
    if (!('speechSynthesis' in window)) { setOpen(true); return }
    if (playing) { window.speechSynthesis.cancel(); setPlaying(false); return }
    const u = new SpeechSynthesisUtterance(audio.script); u.rate = 1.03
    u.onend = () => setPlaying(false); window.speechSynthesis.speak(u); setPlaying(true)
  }
  const stop = () => { if (el.current) { el.current.pause(); el.current.currentTime = 0 } window.speechSynthesis?.cancel(); setPlaying(false) }
  return (
    <div className="rounded-2xl border border-line bg-card p-3">
      <div className="flex items-center gap-3">
        <button type="button" onClick={toggle} className="flex size-10 items-center justify-center rounded-full bg-ink text-paper" aria-label={playing ? 'Pause briefing' : 'Play briefing'}>
          {playing ? <Pause size={16} /> : <Play size={16} className="ml-0.5" />}
        </button>
        <div className="flex-1">
          <div className="text-sm font-semibold">Listen: why this needs you <span className="font-normal text-muted">· ≈1 min</span></div>
          <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-paper">
            <div className="h-full rounded-full bg-accent transition-[width]" style={{ width: dur ? `${(100 * t) / dur}%` : playing ? '100%' : '0%' }} />
          </div>
        </div>
        <button type="button" onClick={stop} className="text-muted hover:text-ink" aria-label="Stop"><Square size={14} /></button>
      </div>
      {audio.src && <audio ref={el} src={audio.src} preload="metadata" onPlay={() => setPlaying(true)} onPause={() => setPlaying(false)}
        onTimeUpdate={e => setT(e.currentTarget.currentTime)} onLoadedMetadata={e => setDur(e.currentTarget.duration)} />}
      <div className="mt-2 flex items-center justify-between text-xs text-muted">
        <span>Synthesized from the review record — <b>not evidence</b>.</span>
        <button type="button" className="underline-offset-2 hover:underline" onClick={() => setOpen(!open)}>{open ? 'hide' : 'show'} transcript</button>
      </div>
      {open && <p className="mt-2 text-sm text-muted">{audio.script}</p>}
    </div>
  )
}

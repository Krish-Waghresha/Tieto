import { useEffect, useState } from 'react'
import type { Excerpt } from '../lib/ledger'

type Tok = { content: string; color?: string }
let hlPromise: Promise<(code: string, lang: string) => Tok[][]> | null = null

// Shiki fine-grained: core + JS regex engine + C# + one theme. Tokens are rendered as React spans
// (codeToHtml would write style="" attributes, which the strict CSP blocks).
function highlighter() {
  if (!hlPromise) {
    hlPromise = (async () => {
      const [{ createHighlighterCore }, { createJavaScriptRegexEngine }, cs, theme] = await Promise.all([
        import('shiki/core'), import('shiki/engine/javascript'), import('shiki/langs/csharp.mjs'), import('shiki/themes/github-light.mjs'),
      ])
      const hl = await createHighlighterCore({ themes: [theme.default], langs: [cs.default], engine: createJavaScriptRegexEngine() })
      return (code: string, lang: string) =>
        lang === 'csharp' ? hl.codeToTokens(code, { lang: 'csharp', theme: 'github-light' }).tokens.map(l => l.map(t => ({ content: t.content, color: t.color })))
          : code.split('\n').map(l => [{ content: l }])
    })()
  }
  return hlPromise
}

export function CodeExcerpt({ ex, lang, tone = 'after', title, maxLines = 18 }: {
  ex: Excerpt; lang: string; tone?: 'before' | 'after'; title?: string; maxLines?: number
}) {
  const [toks, setToks] = useState<Tok[][] | null>(null)
  const code = ex.lines.join('\n')
  useEffect(() => { let live = true; highlighter().then(h => live && setToks(h(code, lang))); return () => { live = false } }, [code, lang])
  const rows: Tok[][] = (toks ?? ex.lines.map((l): Tok[] => [{ content: l }])).slice(0, maxLines)
  const [f0, f1] = ex.focus
  const band = tone === 'after' ? 'bg-accent-soft border-accent' : 'bg-risk-soft border-risk'
  return (
    <figure className="overflow-hidden rounded-xl border border-line bg-card">
      {title && <figcaption className="flex items-center justify-between border-b border-line px-3 py-1.5 font-mono text-[11px] text-muted">{title}</figcaption>}
      <pre className="overflow-x-auto py-2 font-mono text-[12.5px] leading-[1.55]">
        {rows.map((line, i) => {
          const n = ex.start + i
          const hot = n >= f0 && n <= f1
          return (
            <div key={i} className={`flex border-l-[3px] pr-3 ${hot ? band : 'border-transparent'}`}>
              <span className="w-11 shrink-0 select-none pr-3 text-right text-muted/60">{n}</span>
              <code className="whitespace-pre">{line.map((t, j) => <span key={j} style={t.color ? { color: t.color } : undefined}>{t.content}</span>)}</code>
            </div>
          )
        })}
        {ex.lines.length > maxLines && <div className="pl-14 text-muted">… {ex.lines.length - maxLines} more lines</div>}
      </pre>
    </figure>
  )
}

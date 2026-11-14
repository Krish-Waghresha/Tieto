> **STATUS: RESEARCH FINDINGS — NOT FINAL.** UI research wave, 2026-11-14 (agent output; screenshots of public pages for internal design reference only).

# Decision-First Review UI stack (researched 2026-11-14)

## Verdict
**React 19 + Vite 8 + TypeScript + Tailwind v4 + shadcn/ui + @xyflow/react (dagre layout) + Shiki core (C# only) + Motion (LazyMotion) + lucide-react**, built to ONE `index.html` template with `vite-plugin-singlefile`. Python then injects the ledger JSON and a hash-based CSP. **We verified this with a spike** in `/tmp/junction-research/ui-spike/`: it renders offline from `file://` under `default-src 'none'`, with zero CSP violations in headless Chrome.

Why React over Preact, Alpine/Petite-Vue or Svelte: React Flow, shadcn/ui and Motion are all React-first. Those three give us 80% of the "polished" look for free. Preact/compat would save about 40 KB, but compat edge cases cost time we don't have. Alpine and Petite-Vue have no graph or component ecosystem. Svelte has Svelte Flow, but no shadcn-equivalent maturity, and the team is likely faster in React.

## Versions (npm, today)
| pkg | ver |
|---|---|
| vite / @vitejs/plugin-react | 8.3.8 / 6.3.0 |
| vite-plugin-singlefile | 2.3.4 |
| react / react-dom | 19.3.1 |
| typescript | 7.0.2 |
| tailwindcss / @tailwindcss/vite | 4.3.5 |
| shadcn (CLI) | 4.23.0 |
| @xyflow/react | 12.12.1 |
| @dagrejs/dagre | 3.1.3 |
| shiki | 4.6.0 |
| motion | 14.14.0 |
| lucide-react | 1.73.0 |
| @fontsource-variable/inter | 5.3.0 |

## Measured sizes (minified with rolldown)
| piece | raw | gzip |
|---|---|---|
| react-dom | 220 KB | 67 KB |
| @xyflow/react (incl. react) | 195 KB | 63 KB |
| dagre | 47 KB | 16 KB |
| **elkjs bundled** | **1,465 KB** | 444 KB |
| Shiki core + JS regex engine + C# + 1 theme | 270 KB | 67 KB |
| motion `motion.*` / `LazyMotion+m` | 153 / 100 KB | 51 / 35 KB |
| mermaid.min.js | **5.5 MB** | n/a |
| cytoscape.min.js | 443 KB | n/a |
| diff2html-ui.min.js (bundles highlight.js) | 1.05 MB | n/a |
| Inter variable woff2, latin subset | 48 KB (64 KB as base64) | n/a |

**Spike output:** React + React Flow + dagre + Tailwind + lucide + motion + Shiki(C#) gave a single `index.html` of **901 KB raw / 271 KB gzip**. Removing Shiki brings it to 632 KB, and also removing motion brings it to 484 KB.

## Decisions per area
1. **Single file.** `vite-plugin-singlefile` inlines the entry JS as one `<script type="module">` and all CSS as one `<style>`. Dynamic imports are inlined too. It does nothing about CSP, but the output is a fixed set of 1 script + 1 style, so `sha256` hashes work and **'unsafe-inline' is not needed**. The ledger goes in `<script id="ledger" type="application/json">`. CSP does not apply to non-executed data blocks, so the hashes stay valid whatever ledger is injected. Runtime injection is better than build-time: one build, and the Python bot just does a string replace. No Node is needed in the bot.
2. **Components.** Use **shadcn/ui** (CLI `npx shadcn@latest init -t vite`; it copies components into `src/components/ui`). It works natively with Vite + Tailwind v4 and needs the `@` alias in tsconfig and vite.config. Tailwind v4 compiles to one static CSS file that inlines fine, at about 10–30 KB used. Add only Card, Badge, Tabs, Accordion, Tooltip, Progress, Checkbox, Button, RadioGroup (for the quiz and sign form). For charts and badges, skip Tremor (still v3, Tailwind v3 era): coverage bars and tier badges are 10 lines of Tailwind each. Radix Themes is fine but more opinionated and heavier. Mantine 9 brings its own CSS system and is heavier. HeroUI, Park UI and Ark are viable but give no speed win over shadcn.
3. **Graph.** Use **React Flow + dagre**. Custom nodes are plain React. Built-in `animated` edges give the "marching ants" effect, and the dropped path is styled via `style`/`className` per edge. ELK has better layouts but costs 1.46 MB, which is overkill for 12 nodes. d3-dag is fine but needs a hand-rolled renderer. Mermaid (5.5 MB) and Cytoscape (443 KB, canvas, no React nodes) are worse fits. Hand-made SVG is a fallback (see below).
4. **Code and diff.** Use **Shiki fine-grained** (`shiki/core` + `createJavaScriptRegexEngine` + `langs/csharp` + one theme), rendered via **`codeToTokens` into React spans**. That gives our own side-by-side grid, line highlights and annotation callouts. **Do not use `codeToHtml` + `dangerouslySetInnerHTML`**: in the spike, its inline `style=""` attributes triggered 8 `style-src-attr` CSP violations. The token approach sets styles via the CSSOM, which CSP allows. Option to save 270 KB: tokenize in Python with Pygments and ship tokens inside the ledger. Rejected options:
   - Monaco: multi-MB, workers.
   - CodeMirror merge: about 300 KB+, editor UX we don't need.
   - diff2html: 1 MB with highlight.js.
   - Code Hike: needs an MDX pipeline, and its v1 repo is archived.
   - @git-diff-view/react 0.1.8 and react-diff-view 3.3.3: OK for real unified hunks, but not CSP-tested.
5. **Polish.** Use `motion` with `LazyMotion features={domAnimation}` + `m.div` (saves 53 KB) and lucide-react (tree-shaken per icon). For fonts, `@fontsource-variable/inter` latin; Vite inlines the woff2 as a data: URI because of `assetsInlineLimit`. That is 64 KB and needs `font-src data:`. Geist (1.9.2) works the same way.
6. **Audio.** The Web Speech API costs 0 bytes and works offline with OS voices, but voice quality varies by machine and Chrome's "Google" voices need network. Pre-generated TTS sounds better: about 90 s of mono Opus/WebM at 24 kbps is about 270 KB (360 KB as base64), or MP3 at 32 kbps about 360 KB (480 KB as base64). Needs `media-src data:`. Recommendation: embed a pre-generated clip, with Web Speech as the fallback button if the ledger has no audio. Build the player from a native `<audio>` + shadcn Button/Slider, plus a fake waveform from precomputed peaks (Python computes about 100 RMS values into the ledger, rendered as SVG bars). Don't add wavesurfer.
7. **Budget.** Spike 901 KB, + shadcn/Radix pieces about 80 KB, + font 64 KB, − LazyMotion 53 KB gives **about 1.0 MB without audio and about 1.4–1.5 MB with audio** (about 0.35 MB gzip before audio). Artifacts are zipped, so this is comfortable.

## Project structure
```
ui/
  index.html            # <!--CSP--> marker + ledger data block
  vite.config.ts
  src/main.tsx  src/App.tsx  src/ledger.ts (types + loader)
  src/components/ui/*   # shadcn
  src/components/{FlowDiff,CodeExcerpt,Evidence,Coverage,Quiz,AudioPlayer,SignForm}.tsx
  dev-ledger.json       # used by `vite dev`
bot/render_report.py    # inject ledger + CSP
```
Build: `cd ui && npm ci && npx vite build`, then `python -I bot/render_report.py ui/dist/index.html ledger.json report.html`. Commit `ui/dist/index.html` as the template, so the bot (and CI) never needs Node.

## (a) vite.config.ts
```ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { viteSingleFile } from 'vite-plugin-singlefile'
import path from 'node:path'
export default defineConfig({
  plugins: [react(), tailwindcss(), viteSingleFile({ removeViteModuleLoader: true })],
  resolve: { alias: { '@': path.resolve(__dirname, 'src') } },
  build: { assetsInlineLimit: 100_000_000, cssCodeSplit: false, modulePreload: false },
})
```
index.html contains `<!--CSP-->` in `<head>` and `<script id="ledger" type="application/json">__LEDGER__</script>` in body.

## (b) Custom node + dropped path (verified in spike)
```tsx
type D = { label: string; state: 'kept'|'dropped'|'added' }
function StepNode({ data }: NodeProps<Node<D>>) {
  const c = { kept:'border-slate-300 bg-white', dropped:'border-rose-500 bg-rose-50 line-through',
              added:'border-emerald-500 bg-emerald-50' }[data.state]
  return <div className={`rounded-lg border-2 px-3 py-2 text-sm shadow-sm ${c}`}>
    <Handle type="target" position={Position.Top}/>
    {data.state==='dropped' && <ShieldAlert className="inline size-4 text-rose-600 mr-1"/>}{data.label}
    <Handle type="source" position={Position.Bottom}/></div>
}
const nodeTypes = { step: StepNode }   // module scope!
function layout(nodes: Node<D>[], edges: Edge[]) {
  const g = new dagre.graphlib.Graph().setGraph({ rankdir:'TB', nodesep:30, ranksep:50 }).setDefaultEdgeLabel(()=>({}))
  nodes.forEach(n => g.setNode(n.id, { width:170, height:40 })); edges.forEach(e => g.setEdge(e.source, e.target))
  dagre.layout(g)
  return nodes.map(n => { const p = g.node(n.id); return { ...n, position:{ x:p.x-85, y:p.y-20 } } })
}
const dropped = { stroke:'#e11d48', strokeDasharray:'6 4' }
const edges: Edge[] = [
  { id:'ab', source:'a', target:'b', style: dropped },           // removed authZ path
  { id:'bc', source:'b', target:'c', style: dropped },
  { id:'ac', source:'a', target:'c', animated:true, style:{ stroke:'#059669', strokeWidth:2 } }, // new path
]
<ReactFlow nodes={layout(nodes, edges)} edges={edges} nodeTypes={nodeTypes} fitView
  nodesDraggable={false} proOptions={{ hideAttribution: true }}><Background/></ReactFlow>
```
For before/after, render two `<ReactFlow>`s side by side (each needs a fixed-height parent, and import `@xyflow/react/dist/style.css`), or one merged graph coloured by `state`. Hover highlighting: keep `hoveredId` in state and map edges to `{...e, animated: onPath(e)}`.

## (c) Python injection (verified: `</script>` in the ledger is neutralised)
```python
import base64, hashlib, json, re
from pathlib import Path
def _h(s): return "'sha256-" + base64.b64encode(hashlib.sha256(s.encode()).digest()).decode() + "'"
def render(template: Path, ledger: dict, out: Path) -> None:
    html = template.read_text(encoding="utf-8")
    js  = re.findall(r'<script type="module"[^>]*>(.*?)</script>', html, re.S)
    css = re.findall(r'<style[^>]*>(.*?)</style>', html, re.S)
    csp = ("default-src 'none'; img-src data:; font-src data:; media-src data:; "
           f"script-src {' '.join(map(_h, js))}; style-src {' '.join(map(_h, css))}; "
           "base-uri 'none'; form-action 'none'")
    data = json.dumps(ledger, ensure_ascii=False).replace("<", "\\u003c")
    html = html.replace("<!--CSP-->", f'<meta http-equiv="Content-Security-Policy" content="{csp}">', 1)
    out.write_text(html.replace("__LEDGER__", data, 1), encoding="utf-8")
```
The front end reads it with `JSON.parse(document.getElementById('ledger')!.textContent!)`. Inject the ledger last: the regex hashes the template's exact bytes, so never reformat the HTML after hashing.

## Risks
- **CSP style attributes:** any library that writes `style="..."` via innerHTML or setAttribute breaks under strict CSP. React `style={{}}`, React Flow and Motion are fine (CSSOM). Verify each new lib with the spike's `securitypolicyviolation` listener (`document.body.dataset.csp`).
- A meta CSP can't use `frame-ancestors` or `report-uri`; that's acceptable.
- Top-level `await` (Shiki init) needs a modern browser; fine for the demo.
- Don't add Mermaid, ELK, Monaco or diff2html: each blows the budget.
- Payload size: base64 audio dominates. Keep it under 2 min, mono, low bitrate.
- shadcn's `init` asks questions and writes `components.json`. Do it once and commit.
- These versions are very new (Vite 8, TS 7, React Flow 12.12); pin them with a lockfile.

## Fallback if time runs out
Keep the current Python-generated HTML, but adopt the same template trick: a hand-written `report.html` with Tailwind's compiled CSS pasted in once (or plain CSS), and about 200 lines of vanilla TS/JS. The graph becomes **hand-made SVG**: Python computes the dagre-like positions (ranks = topological depth, which is enough for 12 nodes) and emits `<path>`s, with the dropped path as `stroke-dasharray` and animation via a CSS `@keyframes` on `stroke-dashoffset` inside the hashed `<style>`. For code, use Pygments HTML with `noclasses=False` (classes, not inline styles, so it's CSP-safe), plus `<details>` for findings. That needs zero JS dependencies and is about 100 KB.

Sources: shadcn Vite install docs (ui.shadcn.com/docs/installation/vite); Code Hike v1 docs and blog (React + MDX required, repo archived); npm registry for versions; spike measurements.

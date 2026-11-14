> **STATUS: RESEARCH PROPOSAL — NOT FINAL.** UI direction for the review experience, synthesised from three research agents (2026-11-14): [inspiration](../findings/ui/ui-inspiration.md), [design principles + wireframes](../findings/ui/ui-design.md), [tech stack + verified spike](../findings/ui/ui-stack.md). Screenshots: [../findings/ui/screenshots/](../findings/ui/screenshots/).

# Review UI spec — "a guided review, not a report"

## 1. Diagnosis of the current page

The current HTML report (screenshot `pr1b/top.png`) puts a 9-link nav, the to-do list, the summary, the evidence bar, the scope check and a rules table **all above the first scroll, with equal weight** — and shows the bot's read before the reviewer forms their own. It is correct, but it reads like an audit log.

## 2. Direction (recommended)

**A 7-step guided review, styled like an editorial explainer, with a full-page mode for reading at your own pace.**

| Borrowed from | What we take |
| --- | --- |
| **Crux** ([screenshot](../findings/ui/screenshots/crux-demo-03.png)) | Warm paper / dark-ink palette, monospace metadata labels, "Step 2 of 4" stepper *inside* the code card, highlighted lines = tinted band + thin left bar, one-question-per-screen quiz with a 4-dash progress bar |
| **Thariq Shihipar's HTML PR writeup** ([screenshot](../findings/ui/screenshots/thariq-17-pr-writeup.png)) | TL;DR box with a coloured left rule; twin **BEFORE / AFTER** cards (= our decision card); "in this PR" side TOC; numbered "Where to focus" list; files ordered for reading, not alphabetically |
| **Thariq flowchart / code-understanding** | Failure paths dashed red; click node → side panel; changed node tinted. (Their own example overlaps nodes → we lay out with dagre and check by eye.) |
| **CodeRabbit blast radius** | Selecting a finding lights up its path in the graph and dims the rest |
| **DeepWiki** | Every claim ends with a small source chip (`file:lines`) |
| **CodeHike / Stripe docs** | Sticky code pane on one side while steps change on the other |

Rejected for the demo: a Linear-style dashboard (calm but no narrative, weak on a projector).

## 3. The seven steps (one screen each)

Research basis: Shneiderman "overview first, details on demand"; staged disclosure (NN/g); ~4 chunks per screen (Cowan 2001); **pick before reveal** — AI explanations raise over-reliance (Bansal et al. CHI 2021) and cognitive forcing reduces it (Buçinca et al. CSCW 2021), but users dislike friction, so forcing = **one tap**.

| Step | Question it answers | Visual | Interaction |
| --- | --- | --- | --- |
| 1 Verdict | "How worried should I be, and is it my call?" | ◆◆ DEEP badge, owner, one-sentence read, **scope meter** (2 needed vs 28 affected, 14×), **trust bar**, "checks run 0/6" | Start review → |
| 2 What changed | "What does the system do differently now?" | Flow graph with **Before / After toggle**; the 28 call sites as one node "×28"; only the DROPPED path accented | toggle, click node → side panel with code excerpt |
| 3 Decisions | "Do I agree with each choice?" | D1 first (policy), D3/D4 shown as "depends on D1", then D2; twin BEFORE/AFTER cards; source chips | **your pick first**, then AI recommendation unlocks |
| 4 AI found / won't decide | "Is the finding real? What's left to me?" | F1 card with its tool facts and the tests that try to disprove it; ✋ A1, A2 | Looks real / Not an issue / Ask for a test |
| 5 Evidence & gaps | "What was actually checked?" | Ladder bar by grade; checks table; **not run is never hidden** | click a grade to filter |
| 6 Quick check (skippable) | "Did I get the important part?" | 3 consequence questions, one per screen, feedback links back to the graph | Skip always available |
| 7 Sign | "What exactly am I signing?" | "you vs AI" per item, open gaps, residual risk text | generates `/sign` text; submit as PR review |

**PR comment** stays ≤ 4 lines + collapsibles: badge · owner · checks · one sentence · "Start review (≈6 min) →" · "▶ 55 s briefing".

## 4. Visual grammar

| Grade | Icon | Colour (Okabe–Ito) | Line |
| --- | --- | --- | --- |
| Checked by tool | ✔ | blue #0072B2 | solid, filled |
| Test result | ▲ | green #009E73 | solid, outline |
| Tool estimate | ◆ | orange #E69F00 | dashed |
| AI reasoning | ~ | purple #CC79A7 | dotted |
| AI won't decide | ✋ | black | double |
| Not run | ░ | grey | hatched |

- Trust bar order **is** the ladder (strong → gaps); never a single percentage.
- Tier badge: shape count (◇ / ◆ / ◆◆) in one neutral colour — red would read as a verdict.
- Graph: unchanged edges grey; new edge heavier; **DROPPED** path vermillion #D55E00, dashed, ✕ end marker, label on the edge (spatial contiguity — strongest Mayer effect).
- Never meaning by colour alone; icons + words everywhere.

## 5. Audio and quiz

- Audio: ≤ 60 s, the *why* only, never reads code, never autoplays, transcript collapsed while playing (Mayer redundancy). Pre-generated clip embedded (~360 KB Opus) with Web Speech fallback. Plays over the step-2 graph.
- Quiz: framed "check your read", consequence questions, answer keys from tool facts/tests, result recorded, never gates.

## 6. Tech stack (verified by a spike build)

React 19 + Vite 8 + TypeScript + Tailwind 4 / shadcn/ui · `vite-plugin-singlefile` · `@xyflow/react` + `@dagrejs/dagre` · Shiki (C# only, rendered via `codeToTokens` → React spans) · `motion` (LazyMotion) · lucide · Inter embedded.

- **One self-contained HTML file**, opens offline and as an Actions artifact; **strict hash-only CSP, zero violations** in the spike ([screenshot](../findings/ui/screenshots/spike-react-flow-csp.png)).
- Built **once**; the Python bot only injects `<script id="ledger" type="application/json">` + CSP hashes → the bot never needs Node.
- Size ≈ **1.0 MB** (≈ 1.4 MB with audio). Rejected: Mermaid 5.5 MB, ELK 1.46 MB, diff2html 1.05 MB, Monaco.
- Gotcha: anything writing `style=""` attributes breaks the CSP (Shiki's `codeToHtml` did) — test each library.
- **Fallback:** keep Python HTML, same CSP trick, hand-laid SVG graph, Pygments class mode (~100 KB, no JS deps).

## 7. Pitfalls to design against

- **Aesthetic-usability effect:** polish makes weak evidence look strong → "not run" and gaps always on step 1 and step 5.
- Dashboard overload; colour-only meaning; animation that distracts (motion only for the step transition and the dropped-path reveal).
- Long AI rationale → max 2 sentences per card, rest behind "more".

## 8. Proposed split of work

| Who | What |
| --- | --- |
| Implementation track | React app (7 steps + full-page mode) reading `ledger.json`; build to one file |
| Research track | Ledger fields the UI needs (`summary`, owner, ordered decisions, graph nodes/edges with positions or dagre input); audio script + clip; wireframe review with a fresh-eyes tester |
| Both | 5-minute demo walk: step 1 → 2 (toggle) → 3 (pick, unlock) → 4 (F1) → 7 (sign) |

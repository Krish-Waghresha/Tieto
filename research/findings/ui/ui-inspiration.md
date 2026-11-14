> **STATUS: RESEARCH FINDINGS — NOT FINAL.** UI research wave, 2026-11-14 (agent output; screenshots of public pages for internal design reference only).

# UI inspiration for Decision-First Review (2026-11-14)

All screenshots are in `screenshots/`. They were captured with headless Chrome. Crux's animated demo needed a CDP script, which is at `/tmp/junction-research/scripts/ui/cdp.mjs`.

## Where we are

Our current report (`pr1b/top.png`) has the right content, but it looks like a GitHub README. Specifically:
- It has 9 equal-weight anchor links.
- Every section is a bordered card.
- The emoji chips are visually noisy.
- The evidence bar is unlabelled and sits detached from the content.
- The "Why this tier" table opens the page, before the reviewer knows what they are deciding.
- Nothing tells the presenter "you are on step 2 of 5".

The content survives. The work is hierarchy, pacing and calm.

## Crux in depth

Screenshots: `crux-home.png`, `crux-demo-02..05.png`.

- **Palette.** The page is warm paper (#F0ECE4-ish) with near-black ink. There is one accent, a deep teal-blue (#1B5E7E), used for the CTA, the highlighted words in the headline, and the active step. The app mock is dark brown-black, not pure black.
- **Type.** Headings use a humanist sans (IBM Plex Sans style), heavy and tightly tracked. All labels, nav, buttons and metadata use a small monospace with wide letter-spacing ("START FREE", "Step 2 of 4", "4 of 4 questions"). That mono-for-metadata split is most of the "engineered" feel.
- **Hero stepper.** Five steps (01 Connect → 05 Master) sit on a thin horizontal rail. The active step has a hollow ring and a filled line segment, with a "⏸ 03 / 05" pill at the bottom right. It auto-advances.
- **Course page** (`crux-demo-03`):
  - It is a single centred column about 720px wide.
  - At the top: a back link, the title, tag chips (`architecture`, `api`), then "Skip to quiz →" and "Page 2 of 3".
  - The code card has the file path in a mono caps header and "← Step 2 of 4 →" arrows inside the card header. Highlighted lines get a tinted band plus a 2px left accent bar.
  - The explanation sits under the code as a callout with a left border, and it fades/blurs in after the code.
  - Previous / Next page buttons sit at the bottom.
  - Note: it is code, then explanation, stacked vertically, not side by side.
- **Quiz** (`crux-demo-04`). There is one question per screen, and a segmented progress bar of four dashes at the top right. The ordering question uses draggable rows with numbers and grip dots, and a single big "SUBMIT ANSWERS" button. There is lots of empty space.
- **Mastery heatmap** (`crux-demo-05`). A GitHub-contribution-style grid with domains as rows and weeks as columns, coloured in 4 teal steps. It has a "Depth: Structure" dropdown and a quiet sidebar.
- **What to borrow:**
  - paper background with a single accent;
  - mono metadata labels;
  - "Step n of m" inside the card;
  - highlighted line band plus left bar;
  - delayed reveal of the explanation;
  - one question per screen with dash progress.

## Product table

| Product | What it does visually well | What we should copy | Screenshot |
|---|---|---|---|
| Crux | Calm paper palette, mono labels, stepper, step-in-card code walkthrough, one-question quiz | Overall tone; stepper; quiz screen | `ui/crux-home.png`, `ui/crux-demo-03.png`, `ui/crux-demo-04.png`, `ui/crux-demo-05.png` |
| Thariq: PR review (03) | Header card, "What this PR does" bullets, **risk map** of file chips coloured safe/worth a look/needs attention, findings as cards tethered under the diff with a coloured left rule and BLOCKING/NIT labels | Risk-map chips → our evidence chips; findings tethered to lines | `ui/thariq-03-code-review-pr.png` |
| Thariq: PR writeup (17) | **TL;DR box with an orange left rule**, **BEFORE / AFTER twin cards** (after has a green border), files ordered "for reading", a numbered "Where to focus" list, sticky "In this PR" TOC | Exactly our decision card: before/after twin panels plus numbered focus | `ui/thariq-17-pr-writeup.png` |
| Thariq: code understanding (04) | Small box-and-arrow request path with **one node tinted** (the trust boundary); numbered callstack with collapsible source; right rail "Key files" plus "Gotchas" in a warm red card | Tinted changed node; right rail for "AI won't decide" | `ui/thariq-04-code-understanding.png` |
| Thariq: flowchart (13) | Clickable nodes with a detail panel on the right; **dashed red failure paths**, green terminal, legend under the chart. (Note: one overlapping node, so hand-check layouts.) | Click a node to get a side panel; dashed red = dropped path | `ui/thariq-13-flowchart.png` |
| CodeRabbit Change Stack / Blast Radius | Dark graph; the finding list (F1 HIGH in a filled red row) highlights its **path across components** in salmon while the rest dims; node chips CHANGED / UPSTREAM / POTENTIALLY IMPACTED; numbered layer rail 1–11 | Select a finding to light up the path and dim the rest; numbered layer rail | `ui/coderabbit-blast-radius-finding-path.jpg`, `ui/coderabbit-home.png` |
| Graphite AI review | Dark, single focused diff card; finding has a category tag ("Logic bug") plus a suggested-change mini diff plus a primary action | Category tag plus one action per finding | `ui/graphite-review.png` |
| Greptile | Overview comment: Summary → Key changes → Critical issues; 0–5 confidence score; auto-picks diagram type (sequence, ER, flow) | Verdict plus "issues found" ordering; choose diagram by change type | `ui/greptile-summary.png` |
| GitHub new Files changed | Resizable tree with comment/annotation badges per file, "0/210 viewed", split/unified toggle | "n of m viewed" progress; badges in the nav | `ui/github-files-changed.png` |
| Reviewable | Per-file reviewed state, line-mapped discussions, explicit "completion condition" | Sign-off as an explicit condition with its own state | `ui/reviewable-home.png` |
| Linear | Near-black, low-contrast greys, 1px hairlines, properties rail on the right, tiny status icons, no card borders | Right properties rail (tier, owner, checks); hairlines instead of boxes | `ui/linear-home.png` |
| Vercel | Huge tight headline, tabbed "Create / Verify / Deploy" steps, monochrome with a green status. (The deployment page itself needs login, so only the docs were captured.) | Status-dot verdict; tabbed steps | `ui/vercel-deployments-docs.png` |
| DeepWiki | Every claim followed by grey **source pills** (`file.json 1–52`); left nav, right "on this page" | Evidence pill with file plus line range on every claim | `ui/deepwiki-diagram.png`, `ui/deepwiki-react.png` |
| Stripe docs | Prose left, **sticky code pane right** (navy) with file tabs; numbered step circles; the code pane follows the step | Sticky right code pane synced to steps | `ui/stripe-docs.png` |
| CodeHike scrollycoding | Step cards on the left; the active card gets a blue left bar; sticky code on the right animates token transitions between steps | Same, for walking decisions D1→D2 | `ui/codehike-scrolly.png` |
| Sourcegraph | Not captured; the public site is marketing only. Known for hover-cards on symbols and "find references" counts. | "28 call sites" as a hover reveal | — |

## Patterns to steal

1. **Layout grid.** A 12-column grid with a max width of 1200. Main column is 8 cols (~720px reading width, as in Crux, Thariq and Stripe). The right rail is 4 cols, sticky, and holds tier, owner, checks run, evidence legend, and "AI won't decide". In walkthrough steps, switch to 5/7: explanation left, sticky code or graph right.
2. **Verdict-first header.** One line with a status dot, the verdict ("Needs your decision on 4 items"), and the tier pill. Below it, mono metadata (`MP-2283 · PR #1 · 4d44f8b → d91a9e3`). Below that, a TL;DR box with an orange left rule (Thariq 17), holding 2 sentences only. Move "Why this tier" into the rail, collapsed.
3. **Progress and step navigation.** A Crux-style horizontal rail: `01 Decide D1 · 02 Check F1 · 03 Residual A2 · 04 Quiz · 05 Sign`. Use a hollow ring for current, filled for done, and an "03 / 05" pill. Add keyboard ←/→ (great live). Show GitHub-style "2 of 4 decided" in the header.
4. **Side-by-side code plus explanation.**
   - Sticky code pane on the right, with the file path in a mono caps header and "Step 2 of 4" arrows.
   - Highlight lines with a 12%-tint band plus a 2px accent left bar.
   - Dim non-relevant lines to 40% opacity (CodeHike focus).
   - The explanation card on the left is linked to the lines by hover.
5. **Before/after toggle.** Twin cards (BEFORE in neutral grey, AFTER with an accent border) as in Thariq 17, plus a segmented `Before | After | Diff` control on the code pane. In the graph, the same toggle morphs the edges.
6. **Evidence chips.**
   - Drop the emoji.
   - Use 5 chips with a shape and colour pair, so they stay colour-blind safe:
     - solid dot = checked by tool;
     - half dot = tool estimate;
     - dashed outline = AI reasoning, unverified;
     - hand/stop = AI won't decide;
     - hollow = not run.
   - Chip text in 11px mono.
   - Each claim ends with a DeepWiki-style source pill `TypeCollector.cs L239`.
   - The stacked evidence bar should use the same 5 styles and sit in the rail with the legend inline.
7. **Diagram style.**
   - Soft nodes: 8px radius, 1px hairline, white fill.
   - Changed node: tinted fill plus accent border (Thariq 04).
   - Changed path: 2px accent stroke. Everything else is 1px grey at 50%.
   - Dropped path (diagnostics swallowed): **dashed red with a ✕ terminal node** (Thariq 13).
   - Clicking a finding highlights its path and dims the rest (CodeRabbit).
   - Legend under the chart.
   - Hand-lay or use dagre/ELK: Thariq's own example overlaps nodes, and auto-layout glitches look bad on a projector.
8. **Dark/light.** Default to Crux-style warm light paper for the projector; it reads better in bright halls. Offer a `prefers-color-scheme` dark variant. Drive everything from CSS variables (`--paper --ink --muted --accent --ok --warn --risk`). Code blocks stay dark in both modes, which gives the Thariq/Stripe contrast.
9. **Micro-interactions.**
   - Explanation fades in 300ms after the code highlight (Crux).
   - Graph edges draw on step entry (stroke-dashoffset).
   - Chips get a tooltip saying how the claim is known.
   - Quiz answers flip to green/red with a one-line "because L239…".
   - Sign button stays disabled until all decisions are answered, with a progress ring.
   - Audio briefing appears as a slim player bar pinned at the bottom.
   - Respect `prefers-reduced-motion`.

## Design direction: 3 options

**(A) Guided story walkthrough (Crux + CodeHike + Stripe)**
- Full-screen steps: Verdict → D1 → F1 → A2 → Graph → Quiz → Sign. Each step pairs a left explanation with a right sticky code or graph pane. Keyboard ←/→ moves between steps.
- Pros:
  - Perfect pacing for 5 minutes; the presenter clicks through, so there is no scrolling.
  - It makes the "decisions, not diffs" thesis visceral.
  - The quiz and sign-off feel like a payoff.
- Cons:
  - It hides the overview, and judges may ask "where's everything?".
  - More JS and state.
  - Risky if a step breaks live.

**(B) Calm Linear-style dashboard**
- A verdict header, then a list of decisions as rows with status, a right properties rail (tier, owner, evidence bar, checks), and a detail panel that slides in.
- Pros:
  - Looks like a real product.
  - Shows everything at once.
  - Scales to many PRs, which supports the "pilot at Tieto" story.
- Cons:
  - It lacks narrative; in a demo it becomes "and here's another panel…".
  - Dense, and weak on a projector.
  - The flow graph gets squeezed.

**(C) Thariq-style single-page explainer**
- One long, beautifully typeset page:
  - verdict and TL;DR;
  - before/after twin cards per decision;
  - inline graph;
  - findings tethered to code;
  - "won't decide" rail;
  - quiz;
  - sign.
- Pros:
  - The cheapest step from the current HTML (same generator, new CSS).
  - Works as a static artifact, as a GitHub Pages link, and when printed.
  - Honest, document-like, and trust-signalling.
- Cons:
  - Scrolling on stage is clumsy.
  - It feels like "a nicer report", not an experience.

## Recommendation

**Build C as the base and add A as a presenter mode.** Concretely:
- Restyle the existing single page with a Crux paper palette, mono metadata, a verdict-first header, a sticky right rail, Thariq before/after cards, shape-coded evidence chips, and a soft-node graph with a dashed red dropped path.
- Wrap each top-level section in `<section data-step>` and add ~60 lines of JS:
  - a step rail at the top;
  - ←/→ scrolls to and focuses the next section;
  - non-active sections dim to 30%;
  - the graph or code highlights animate on entry.

You keep one artifact that reads well asynchronously, which is what a reviewer actually gets. On stage it becomes a 6-step guided story (Verdict → D1 before/after → graph → F1 → quiz → sign) that fits in 5 minutes with no scrolling. Skip B for the demo, but show one Linear-style "queue" screenshot only if asked about scale.

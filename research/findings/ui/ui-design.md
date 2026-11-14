> **STATUS: RESEARCH FINDINGS — NOT FINAL.** UI research wave, 2026-11-14 (agent output; screenshots of public pages for internal design reference only).

# Making the review report digestible: UI design research

The current page (`pr1b/top.png`) shows everything at once: a 9-link nav, a "what to do" list, a summary, a stacked evidence bar, a scope callout and a rules table, all above the fold. Every item gets equal weight, and the reader is told the verdict before forming their own. The proposal below turns it into a **staged walk-through of 7 screens**. Each screen uses progressive disclosure, and the reviewer commits to a verdict before seeing the AI's.

## 1. Principles (with sources)

| Principle | What it means here | Source |
|---|---|---|
| Progressive disclosure | Show the primary screen first and put details one click away. Whatever appears first signals what matters. NN/g distinguishes *staged* disclosure (everyone steps through) from *progressive* (most never open layer 2). Use staged for the 7 steps and progressive inside each one. | https://www.nngroup.com/articles/progressive-disclosure/ |
| Overview first, zoom and filter, details on demand | Step 1 is the overview. The graph lets you zoom from the aggregate node to the 28 call sites. Code appears on demand. | Shneiderman 1996, https://www.cs.umd.edu/~ben/papers/Shneiderman1996eyes.pdf |
| Inverted pyramid / BLUF | The conclusion and the person who decides come first, background last. | https://www.nngroup.com/articles/inverted-pyramid/ |
| Cognitive load, ~4 chunks | Working memory holds about 4 chunks (Cowan), not 7±2. Keep ≤4 items per screen, which matches the 4 decisions. | https://pubmed.ncbi.nlm.nih.gov/11515286/ |
| Mayer: signalling | Highlight the one thing that matters (the DROPPED path). Supported in 24 of 28 tests. | https://www.cambridge.org/core/books/cambridge-handbook-of-multimedia-learning/principles-for-reducing-extraneous-processing-in-multimedia-learning-coherence-signaling-redundancy-spatial-contiguity-and-temporal-contiguity-principles/CD5B7AE1279A9AB81F8EEBB53DBEC86E |
| Mayer: segmenting | Learner-paced segments beat one continuous stream, which is the case for the step-by-step flow. | same handbook; summary: https://services.dartmouth.edu/TDClient/1806/Portal/KB/PrintArticle?ID=171655 |
| Mayer: spatial contiguity | Put labels on the graph edges, not in a legend below. Strongest effect of the set (9 of 9 tests, d≈1.2). | same chapter |
| Mayer: redundancy | Graphics plus narration beat graphics plus narration plus identical on-screen text. While audio plays, don't show a full transcript beside the graph; keep it collapsed. Very short on-screen labels are fine. | same chapter |
| Pre-attentive attributes | Colour hue, line style and enclosure are detected in under 250 ms. Accent **one** path only, or nothing pops out. | Healey, https://www.csc2.ncsu.edu/faculty/healey/PP/ ; Ware, *Information Visualization* |
| Colour-blind-safe palette | Okabe–Ito: #E69F00 orange, #56B4E9 sky, #009E73 green, #F0E442 yellow, #0072B2 blue, #D55E00 vermillion, #CC79A7 purple, #000 black. Always pair colour with an icon and a line style (WCAG 1.4.1). | https://jfly.uni-koeln.de/color/ ; https://www.w3.org/WAI/WCAG21/Understanding/use-of-color.html |
| Explanations raise over-reliance | Explanations made people accept the AI's answer *whether or not it was right*. Showing confidence did as well as full explanations. So keep AI rationale short and graded. | Bansal et al. CHI 2021, https://arxiv.org/abs/2006.14779 |
| Cognitive forcing functions | Asking people to decide before they see the AI's answer reduced over-reliance. The cost: users liked it less. So make the forcing step a single tap. | Buçinca et al. CSCW 2021, https://arxiv.org/abs/2102.09692 |
| Show uncertainty without false precision | Use ordinal grades (tool-checked > test > estimate > AI reasoning), not "87% confident". | Bansal 2021; Google PAIR, https://pair.withgoogle.com/chapter/explainability-trust/ |
| Retrieval practice | Low-stakes recall improves retention and judgement more than rereading does. | Roediger & Karpicke 2006, https://doi.org/10.1111/j.1467-9280.2006.01693.x |
| What reviewers actually need | The main challenge in code review is *understanding* the change and its context. | Bacchelli & Bird ICSE 2013, https://www.microsoft.com/en-us/research/publication/expectations-outcomes-and-challenges-of-modern-code-review/ |

## 2. The guided review flow (7 steps, one screen each)

| # | Step | Content | Visual | The one question | Interaction |
|---|---|---|---|---|---|
| 1 | Verdict & who decides | Tier, owner, a one-line PR summary, 0/6 checks, scope 2 vs 28 | Tier badge, scope meter, trust bar | "Is this mine to decide, and how deep must I go?" | "Start review"; why this tier sits behind a ⓘ |
| 2 | What changed | A 3-sentence story | Before/after flow graph, aggregate node "28×" | "Do I understand what the code now does?" | Toggle before/after; click 28× to list call sites |
| 3 | Decisions (D1 → D3/D4 → D2) | One decision per sub-screen: before/after, alternatives, requirement trace | Dependency chip "D3, D4 follow D1" | "Which option do I pick?" | **Your pick first**, then the AI's recommendation is revealed |
| 4 | AI found / won't decide | F1 (unconfirmed), A1 and A2 | Grade icon per item | "Do I accept F1 / the residual risk?" | Confirm / dismiss / ask for test |
| 5 | Evidence & gaps | 6 grades, coverage, "not run: 7" | Trust bar, coverage strip | "Is the evidence strong enough to sign?" | Click a segment to filter items |
| 6 | Quick check | 3 questions plus free text | Plain cards | "Did I catch the key risk?" | Skippable; answers shown with feedback |
| 7 | Sign | Summary of my picks vs the AI's, open gaps | Diff of choices | "Am I willing to own this?" | Approve / request changes / escalate |

The left rail shows the steps (●○○○○○○). Audio (▶ 0:55) sits in the header on steps 1–2 only.

## 3. Wireframes

```
GitHub PR comment
┌──────────────────────────────────────────────────────────────────────────────────────┐
│ ◆◆ DEEP REVIEW · owner @area-owner · checks 0/6 run                                  │
│ Fixes the crash (2 sites) but also changes 28 diagnostic call sites; may hide        │
│ real warnings. 4 decisions need you.                                                 │
│ ▸ Start review (≈6 min) →  [step 1]           ▶ 55s briefing                         │
└──────────────────────────────────────────────────────────────────────────────────────┘
Step 1 — Verdict & who decides
┌─ ●○○○○○○ ────────────────────────────────────────────────────────────── ▶ 0:55 ──┐
│ ◆◆ DEEP REVIEW   ⓘ why: R-DIAG-POLICY, R-CROSSCUT                                  │
│ Decides: @area-owner (not the author, not the AI)                                  │
│ Crash fix looks right; extra filter silently drops warnings.                       │
│ SCOPE  needed ██ 2        affected ████████████████████████████ 28   (14×)         │
│ TRUST  ✔✔✔✔✔✔✔ ◆◆ ~~~~~ ✋ ░░░░░░░   checks run 0/6                                 │
│                                                        [ Start review → ]          │
└────────────────────────────────────────────────────────────────────────────────────┘
Step 2 — What changed            [ Before | ●After | Overlay ]
┌─ ○●○○○○○ ──────────────────────────────────────────────────────────────────────────┐
│ ┌─────────┐    ┌──────────────────┐    ┌─────────────┐  ╭─ yes ─▶ warning shown    │
│ │ call    │───▶│ reportDiagnostic │═══▶│ NEW filter  │──┤                         │
│ │ sites 28│    └──────────────────┘    │ in project? │  ╰┄ no ┄┄▶ DROPPED ✕        │
│ └─────────┘ click to expand            └─────────────┘     (vermillion, dashed)    │
│ "Before, every warning reached the user. Now, warnings without a location in       │
│  this project are dropped."                                [ Next: decisions → ]   │
└────────────────────────────────────────────────────────────────────────────────────┘
Step 3 — Decision D1 of 4 (policy)    D3, D4 depend on this
┌─ ○○●○○○○ ──────────────────────────────────────────────────────────────────────────┐
│ BEFORE: all diagnostics reported     │ AFTER: non-project diagnostics dropped      │
│ Options:  (A) keep drop-all   (B) narrow to 2 crash sites   (C) report like #2305  │
│ Trace: MP-2283 asks for crash fix only                                ✔ tool       │
│ Your pick:  [ A ]  [ B ]  [ C ]  [ Unsure ]                                        │
│ ── AI recommendation (locked until you pick) ───────────────────────── 🔒          │
└────────────────────────────────────────────────────────────────────────────────────┘
Step 4 — AI found / won't decide
┌─ ○○○●○○○ ──────────────────────────────────────────────────────────────────────────┐
│ F1 ~ AI reasoning, unconfirmed: positional records may lose MsgPack005             │
│    [ Looks real ] [ Not an issue ] [ Ask for a test ]     ▸ show evidence P4b P4h  │
│ ✋ A1 policy call — yours.   ✋ A2 residual risk — accept or ask for round-trip test│
└────────────────────────────────────────────────────────────────────────────────────┘
Step 5 — Evidence & gaps
┌─ ○○○○●○○ ──────────────────────────────────────────────────────────────────────────┐
│ ✔ tool 7  ▲ test 0  ◆ estimate 2  ~ AI 5  ✋ won't decide 1  ░ not run 7           │
│ ✔✔✔✔✔✔✔◆◆~~~~~✋░░░░░░░   (click a segment to filter)                               │
│ Coverage of changed blocks: ■■■□□□□□ 3/8 blocks tested                             │
│ ⚠ Not run: fail-on-base / pass-on-head (P1, P2)                                    │
└────────────────────────────────────────────────────────────────────────────────────┘
Step 6 — Quick check (optional, 3 Qs)            [ Skip ]
┌─ ○○○○○●○ ──────────────────────────────────────────────────────────────────────────┐
│ Q1 Which warnings does the new filter drop?  ( ) all  ( ) non-project  ( ) none    │
│ ✔ Right: and that's why D1 matters. ▸ see graph                                    │
│ Anything that worried you? [________________________]                              │
└────────────────────────────────────────────────────────────────────────────────────┘
Step 7 — Sign
┌─ ○○○○○○● ──────────────────────────────────────────────────────────────────────────┐
│ D1 you: B  AI: B ✓ │ D2 you: A  AI: C ≠ │ D3 B │ D4 B │ F1: ask test │ A2: accept   │
│ Still open: 7 checks not run.                                                      │
│ [ Request changes ]  [ Approve with noted risk ]  [ Escalate ]   signed as …       │
└────────────────────────────────────────────────────────────────────────────────────┘
```

## 4. Visual grammar

**Evidence grades.** Each grade has an icon, a colour and a line style, so it stays readable in greyscale and to colour-blind readers.

| Grade | Icon | Okabe–Ito | Line/fill |
|---|---|---|---|
| Checked by tool | ✔ | blue #0072B2 | solid, filled |
| Test result | ▲ | green #009E73 | solid, outline |
| Tool estimate | ◆ | orange #E69F00 | dashed |
| AI reasoning | ~ | purple #CC79A7 | dotted |
| AI won't decide | ✋ | black | double |
| Not run | ░ | grey hatch | hatched, empty |

The order of the trust bar *is* the ladder: strongest evidence on the left, gaps on the right, segments sized by count. Never show it as a single percentage.

**Tier badges.** Use shape count plus a word: ◇ LIGHT, ◆ STANDARD, ◆◆ DEEP. Use the same neutral colour for all tiers. The tier is not a danger signal, and red would be read as a verdict.

**Before/after graph.** Default to a **toggle** with an overlay option. A toggle keeps the layout fixed, so the change is the only thing that moves. Side by side halves the width and forces eye travel, and overlay gets noisy. In the overlay, unchanged edges are grey. The new edge is solid blue and heavier. The dropped path is **vermillion #D55E00, dashed, with a ✕ end marker and the label "DROPPED" on the edge** (spatial contiguity). Accent only that one path.

**28 call sites.** Use one aggregate node with a count badge ("call sites ×28") and a stacked-card shadow. Clicking it opens a list grouped by file. The 2 sites the fix needs get an outline so they stand out within the 28.

**Scope meter.** Two bars on a shared axis: "needed 2" filled, "affected 28" outline, plus the ratio "14×". The label carries the ◆ estimate icon, because the count is a tool estimate.

## 5. Quiz and audio

**Quiz.** Retrieval practice works when it is low stakes, gives immediate feedback and asks about *meaning* (Roediger & Karpicke). To avoid sounding patronising:
- ask about consequences ("what happens to a warning from a referenced assembly?"), not trivia;
- frame it as "check your read", never as a test;
- explain every answer and link it back to the graph;
- always offer Skip;
- never block signing; record whether it was skipped.

The free-text field ("anything that worried you?") goes into the signature record. Expect usability cost: Buçinca found that the forcing designs that worked best were liked least. So keep it to 3 questions, under 60 s total.

**Audio.** Narrate ≤60 s of the *why*: the risk, the 4 decisions and who decides. Never read code, hashes or tables aloud. It should play over the step 2 graph (narration + graphic), with the transcript collapsed rather than shown alongside (redundancy principle). Add captions or the transcript for accessibility (WCAG 1.2). Never auto-play.

## 6. Pitfalls

- **Polish that persuades.** A beautiful UI raises perceived credibility ("aesthetic-usability effect", https://www.nngroup.com/articles/aesthetic-usability-effect/). Keep visual weight proportional to the evidence: show AI-reasoning items in lighter, dotted styling. Put "0/6 checks run" next to the verdict, not below it.
- **Dashboard overload.** The current page shows 9 nav targets and 5 kinds of widget above the fold. Limit each screen to about 4 chunks and maximise the data-ink ratio (Tufte, *The Visual Display of Quantitative Information*): no 3D, gradients or decorative icons.
- **Colour-only meaning.** Every colour needs an icon and a line style. Test with a CVD simulator and in greyscale.
- **Distracting animation.** Animate only the before→after toggle, ≤300 ms, and respect `prefers-reduced-motion`. No pulsing alerts.
- **Rationale walls.** Long AI explanations increase blind acceptance (Bansal). Keep each one to a sentence and link out to the evidence.
- **Hidden gaps.** Never collapse "not run" behind progressive disclosure. Gaps belong in the overview.

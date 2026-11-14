# Research track — Earned Trust in AI Code (Tieto, Junction 2026)

> **STATUS: RESEARCH FINDINGS AND PROPOSALS — NOT FINAL.**
> This folder is the research/experiment track (Jakub). It is input for the implementation track, not an agreed design. Nothing here has been executed against the sample repo yet unless explicitly labeled *executed*. Vendor numbers and [UNVERIFIED] items must be checked before use — see `findings/fact-check-waveB.md`.

## Start here

1. [findings/takeaways.md](findings/takeaways.md) — what to take from each company/product, honest positioning, what not to claim
2. [proposal/pipeline.md](proposal/pipeline.md) — **Decision-First Review** pipeline proposal (v0.3, after adversarial review)
3. [proposal/demo-plan.md](proposal/demo-plan.md) — what to actually run on `ju26-issue-2283`, walkthrough, cut list
4. [proposal/decisions-log.md](proposal/decisions-log.md) — lessons & decisions log (observed vs anticipated failures)

## Proposal (not final)

| File | What |
| --- | --- |
| [proposal/pipeline.md](proposal/pipeline.md) | Pipeline v0.3: Pin → Triage → Verify → Extract → Coverage → Brief → Sign → Learn, worked example 2283 |
| [proposal/concept-card.md](proposal/concept-card.md) | Earlier concept card v0.1 (label set superseded by pipeline v0.3; to be aligned) |
| [proposal/demo-plan.md](proposal/demo-plan.md) | Executable proofs P1–P5, JSON-ledger → HTML artifact, 5-min walkthrough |
| [proposal/decisions-log.md](proposal/decisions-log.md) | Decisions, observed failures, open team calls |
| [proposal/ui-spec.md](proposal/ui-spec.md) | Review UI direction: 7-step guided review, visual grammar, verified single-file React stack |

## Findings (not final)

| File | Topic |
| --- | --- |
| [findings/00-landscape.md](findings/00-landscape.md) | Tieto, the bottleneck data, vendors, failure modes, regulation, sample branches, big tech, quant, product gap table, formal methods |
| [findings/waveA-bigtech.md](findings/waveA-bigtech.md) | DoorDash, Uber tooling, Zalando, Rewind, Intercom, Adyen, Monzo, Vercel — 2026 PR risk triage |
| [findings/waveA-trading.md](findings/waveA-trading.md) | Optiver, SIG, HRT, G-Research, Two Sigma; MiFID II RTS 6, ESMA, FCA, SEC 15c3-5, Knight Capital |
| [findings/waveA-safety-critical.md](findings/waveA-safety-critical.md) | DO-178C/330/333, Airbus, Astrée, SCADE, NASA JPL SCRUB, ISO 26262, EASA/FAA on AI |
| [findings/waveA-visualization.md](findings/waveA-visualization.md) | Code graphs (Roslyn, SCIP, NDepend, Understand), PR visualization research, LLM explanation accuracy, comprehension theory |
| [findings/classification-comprehension.md](findings/classification-comprehension.md) | Change-type classification in practice; reviewer comprehension tools |
| [findings/deterministic-classification.md](findings/deterministic-classification.md) | Deterministic signals, proofs of change type, C# analyzers (contains a correction note) |
| [findings/crux-and-video.md](findings/crux-and-video.md) | Crux (kiasm) and Thariq Shihipar's "HTML is the new markdown" |
| [findings/jane-street/](findings/jane-street/) | Jane Street analysis + 8 primary transcripts |
| [findings/video/](findings/video/) | Transcript of "Why this Claude Code engineer uses HTML files as AI specs" (How I AI, 2026-05-18) |
| [findings/wave2-adversarial-reviews.md](findings/wave2-adversarial-reviews.md) | Four adversarial reviews of pipeline v0.2 |
| [findings/fact-check-waveB.md](findings/fact-check-waveB.md) | Fact-check of slide-worthy claims |
| [findings/ui/](findings/ui/) | UI research: inspiration (Crux, Thariq, CodeRabbit, DeepWiki, CodeHike…), design principles + wireframes, tech stack spike, screenshots |
| [findings/wave-postbuild-reviews.md](findings/wave-postbuild-reviews.md) | Security + judge reviews of the end-to-end demo, and what was fixed |

## Demo (reference implementation, not final)

Branches `demo/base` (bot, policy, workflows, base sample), `demo/agent-2283` (agent change), `demo/reports` (rendered report). PR #1: `demo/agent-2283` → `demo/base`.

## Method

- **Research waves:** wave 1 (Tieto, bottleneck, sample repo) → big tech / quant / products → formal methods + Jane Street transcripts → classification / comprehension / Crux / video → wave 2 adversarial review → wave A deep dives (trading, big tech, safety-critical, visualization) → wave B fact-check.
- Sample repo inspected read-only in `/tmp`, never built or run.
- Transcripts are from official/primary transcript pages or YouTube subtitles; third-party summaries are labeled.

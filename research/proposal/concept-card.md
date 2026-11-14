> **STATUS: RESEARCH PROPOSAL — NOT FINAL.** Working draft from the research/experiment track (Jakub). Not an agreed design or implementation spec; claims marked pending/simulated/proposed are unverified.

# Concept Card — Decision-First Review (v0.2, 2026-11-14)

**Machines read the lines. Humans own the decisions.**

Aligned with [pipeline.md](pipeline.md) v0.4. Sources: [takeaways](../findings/takeaways.md), [fact-check](../findings/fact-check-waveB.md).

---

## Problem

> *"I can have 10 Claude codes all writing code, and it doesn't matter. I'm not going to go any faster if I can't merge those PRs after reviewing them and actually deciding they work."* — Will Wilson, Signals and Threads ep. 26

High-AI teams merge 98% more PRs while PR review time rises 91% (Faros AI 2025). Today's best AI reviewers score roughly 50–65% F1 on code-review benchmarks (Martian; secondary sources) — they can **advise**, not **gate**. The two failure modes are a review bottleneck or a rubber stamp: *"the AI said it was fine."*

## Recommendation

Reduce every agent-written PR to **the few decisions the agent made**. Each decision carries before/after behavior, alternatives, graded evidence, and a trace to the requirement — or is openly marked unknown. A **named engineer signs exactly those decisions**. A deterministic **coverage check** proves nothing changed that no decision explains. Every escaped defect is traced to the routing rule that let it through, and that area loses its right to lighter review.

**Flow:** Pin → Triage (deterministic verdict engine) → Verify → Extract decisions → Coverage → Brief (minimal PR card + HTML view) → Sign → Learn.

## One vocabulary

| Grade | Meaning |
| --- | --- |
| **PROVEN** | Deterministic output of a sound/qualified tool on the pinned SHAs — with stated blind spots |
| **MEASURED** | Executed test/run — bounded by its inputs |
| **HEURISTIC** | Rule of thumb (linters, path rules, text search) — known false-positive rate |
| **ARGUED** | LLM interpretation citing hunk/node IDs — never higher, never evidence alone |
| **ABSTAINED** | AI will not decide — says why and what human action resolves it |
| **UNSUPPORTED / UNKNOWN** | Could not analyze or classify — always routed to a human, never a pass |

## Principles

| # | Principle | Balances |
| --- | --- | --- |
| 1 | **AI advises, a named human approves.** The AI never merges, approves, or counts toward required reviewers; the agent's prompter cannot sign. | accountability |
| 2 | **Deterministic verdict, AI as input.** Tiers come from unit-tested rules; LLM output is ARGUED at most (Rewind; DO-330 logic). | confidence, hallucination |
| 3 | **Evidence over confidence.** Every claim carries a grade and a link to its artifact — no unexplained percentages. | transparency |
| 4 | **No self-certification.** Agent-written tests must fail on base and pass on head; the originating failure is re-run (Optiver, Uber FixrLeak). | quality |
| 5 | **Unknown is never a pass.** Abstentions and unsupported analysis are first-class outcomes routed to humans. | risk |
| 6 | **Depth follows risk, not size.** Protected paths and rules each cite their origin (incident or regulation); "the depth of the review shall be proportionate to the magnitude of the proposed change" (RTS 6 Art. 11(1)). | risk, cost |
| 7 | **The model can suggest, but never define.** AI findings must map to a rules index and survive a disprove-it pass before a human sees them (G-Research, DoorDash). | noise, hallucination |
| 8 | **Evidence expires; repo content is untrusted.** New commits invalidate affected items; PR text and code cannot change policy; triage uses the base revision's policy. | security, correctness |
| 9 | **Trust is per area, earned and withdrawn.** Escapes revoke lighter review; policy is periodically re-certified. | scale, risk |

## What is borrowed vs new

- **Borrowed (practicality):** risk routing (Cloudflare, Meta RADAR, Zalando, Rewind, Intercom, Adyen), deterministic verdict engines and protected paths (Rewind), proportionate review (MiFID II RTS 6), per-path ownership (Jane Street Iron), single evidence queue (NASA JPL SCRUB).
- **New:** decisions instead of comments · coverage check for missed decisions · graded evidence with ABSTAINED/UNSUPPORTED · signed decision record feeding per-area trust. No product or published practice we found combines these.

## Worked example — `ju26-issue-2283` (MessagePack-CSharp)

**Requirement #2283:** generator/analyzer crash (`IndexOutOfRangeException`) on closed generic value types from referenced assemblies. **Change:** commit `9df83c38` on base `32258fdb`.

| Item | Content | Status |
| --- | --- | --- |
| Tier | **DEEP** — diagnostic policy in an analyzer; constructor wraps `reportDiagnostic` (`TypeCollector.cs:239`) so all **30 live call sites** pass the new filter (`:1444-1450`) | manually verified |
| D1 | Drop diagnostics without in-compilation location — across 30 sites, not just the 2 crash sites; upstream PR #2305 reports at `Location.None` instead | manually verified |
| D2 | `[0]` → `FirstOrDefault()` + new helper (`:1434`) — the crash fix | manually verified |
| Coverage | Requirement names 2 crash sites; change filters 30 → scope mismatch card | manually verified |
| F1 | New helper ignores the `ParameterSyntax` handling already at `:926` in the base → positional-record MsgPack005 goes from crash to silent drop | ARGUED; P4 test proposed |
| A1 | Drop vs report is a maintainer policy call | ABSTAINED |
| A2 | Generated serializer for unkeyed metadata member unchecked | UNSUPPORTED |
| P1–P3 | New tests pass on head / fail on base / golden suite unchanged | proposed → run |
| Outcome | **Request changes** — keep D2, narrow D1 or adopt #2305, handle `ParameterSyntax` | to be signed by named owner |

## Trade-offs

- **Less reading vs missed defects** — LIGHT routing will let some defects through; we measure escapes and withdraw trust rather than pretend otherwise.
- **Clear explanations vs lost nuance** — ARGUED claims can be persuasive and wrong; uncited sentences are flagged phantom.
- **Deeper analysis vs latency/cost** — replay, mutation and cross-model review only on DEEP.
- **More abstentions vs human load** — abstention rate is tracked; too many makes the reviewer useless, too few makes it dangerous.

## Limits — when not to trust this

- Blind to reflection, DI, dynamic dispatch, external consumers; non-C# languages get no decision extraction.
- Tests, golden files and replay cover only their inputs; CFG facts describe control flow, not correctness.
- A wrong requirement yields a well-evidenced wrong change.
- Visuals aid comprehension; no controlled study shows they raise defect detection.
- No regulator yet defines review of AI-written code; this is a proposal for that gap, not a compliance claim.

## How trust is measured (3-month shadow pilot — targets, not results)

| Metric | Target | Stop rule |
| --- | --- | --- |
| Escapes + reverts + fix-forwards per 100 PRs, by area | not worse than prior 6 months | any Sev1/2 from a LIGHT PR |
| Active review minutes on STANDARD | −30% | +10% after week 6 |
| Triage agreement with humans (before go-live) | ≥90% | area stays in shadow |
| Decision-extraction recall (blind senior reviewer) | ≥85% | <70% |
| Finding precision / "not useful" rate | ≥70% / ≤10% | <50% for 2 weeks |
| DEEP share; median cost per PR | ≤30%; <$5 | >50%; >$15 |

## Who owns what

| Thing | Owner |
| --- | --- |
| Merge decision | Named signer (not the agent's prompter) |
| DEEP co-sign | Owner of the highest-tier path touched |
| `REVIEW_POLICY` | Area owners; changes are DEEP; re-certified periodically |
| Verdict engine + reviewer AI metrics | Platform team |
| Restoring LIGHT after an escape | Area owner, recorded |

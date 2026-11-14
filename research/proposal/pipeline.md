> **STATUS: RESEARCH PROPOSAL — NOT FINAL.** Working draft from the research/experiment track (Jakub). Not an agreed design or implementation spec; claims marked pending/simulated/proposed are unverified.

# Decision-First Review — pipeline design (DRAFT v0.3, 2026-11-14)

> **Machines read the lines. Humans own the decisions.**
>
> Every agent-written PR is reduced to the few choices the agent made, each tied to the requirement and to a check that actually ran — or openly marked unknown. A named engineer signs exactly those choices. Any defect that escapes is traced back to the routing rule that let it through, and that area loses its right to lighter review.

v0.3 incorporates four adversarial reviews (judge, red team, reviewer/operator, demo feasibility) — see [decisions-log.md](decisions-log.md). Research: [findings/00-landscape.md](../findings/00-landscape.md), [findings/](../findings/). Supersedes the label set in [concept-card.md](concept-card.md) (to be aligned).

---

## 1. Moving the center of gravity

| Mode | How a human gets confidence | Who does it today |
| --- | --- | --- |
| Crawl | Read every line | Classic review |
| Walk | Better diffs (semantic, stacked, refactor-aware) | difftastic, Graphite, RAID |
| Run | AI comments on the diff | Copilot, CodeRabbit, Bugbot — best ≈ 50–65% F1 depending on benchmark run (Martian; scores from secondary sources) |
| Bus | Route by risk — **established practice in 2026, not our novelty** | Cloudflare, Meta RADAR, Zalando, Rewind, Intercom, Adyen, gitStream; mandated in trading by MiFID II RTS 6 Art. 11(1) |
| **Plane — this concept** | PR compiled into **decisions**, each with before/after behavior and evidence; a deterministic coverage check guarantees nothing changed that no decision explains | Not found in any product or published practice (research §11–12, classification-comprehension §C) |
| Teleport — *direction, not demonstrated* | Human signs intent + invariants before code is written; merge = checked conformance + sign-off on choices beyond spec | Kiro specs, AWS Cedar point this way |

---

## 2. One vocabulary

**Evidence grade** (every claim carries exactly one):

| Grade | Meaning | Must state |
| --- | --- | --- |
| **PROVEN** | Deterministic tool output on the pinned SHAs | its known blind spots |
| **MEASURED** | An executed test/run | the inputs it covers |
| **HEURISTIC** | Rule of thumb | its known false-positive rate |
| **ARGUED** | LLM interpretation citing hunk/fact IDs | that it is not evidence alone |

**Outcomes** besides a finding: **ABSTAINED** (AI will not decide — why, and what human action resolves it), **UNSUPPORTED** (analysis could not run — routed to human, never a pass).

**Demo status** on every artifact: *executed · manually verified · simulated · proposed.*

---

## 3. Pipeline

```
 PR + requirement ID
 [0] PIN            base/merge-base, head, policy hash, tool versions, provenance
 [1] TRIAGE         deterministic facts → tier LIGHT / STANDARD / DEEP  (no LLM)
 [2] VERIFY         per-tier checks; AI only proposes; unverified → abstention
 [3] EXTRACT        decisions from diff+facts (blind to agent story), then reconcile
 [4] COVERAGE       every hunk & CFG delta claimed by a decision or fact — else card
 [5] BRIEF          decision cards in the PR + HTML view, generated from ledger only
 [6] SIGN           named human, server-side, bound to SHAs → real PR approval
 [7] LEARN          escapes traced to rules; per-area trust; reviewer AI scored
```

### [0] Pin
- Base = merge-base with target branch; record base, head, **policy hash, analyzer-config hash, tool versions**, requirement text, author (agent/model), session log (secret-scanned).
- **Triage always uses the base revision's policy and analyzer config.** A PR cannot change the rules that judge it.
- *Observed failure:* our own research agent diffed `ju26-issue-2283` against the wrong base and blamed the AI for a dependabot Roslyn 4.3→4.12 bump.

### [1] Triage — deterministic, no LLM

| Signal | Grade (with stated limit) |
| --- | --- |
| Build + analyzers (base config) | PROVEN under base config; HEURISTIC if PR touches config |
| Whitespace/non-doc-comment only | PROVEN — **directives, `#pragma`, `#nullable`, doc comments count as changes** |
| Behavior absent | PROVEN only via **identical IL/metadata of every shipped assembly** (deterministic build) |
| Docs/tests paths | PROVEN path membership — *not* absence of behavior change (globs can include test files in shipped projects) |
| Public API diff | PROVEN for signatures — blind to wire format, diagnostic IDs, reflection, `InternalsVisibleTo` |
| Generated (golden) output | MEASURED — bounded to the generator test corpus |
| Dependencies | PROVEN direct; transitive needs lockfile diff |
| Tests removed/skipped | PROVEN; weakened assertions / changed expected values: HEURISTIC → always a decision card |
| Blast radius (`SymbolFinder`, CFG diff) | PROVEN **lower bound** — misses reflection, DI, delegates, external consumers |
| Self-written tests | HEURISTIC unless commits signed + provenance attested |
| JIT risk (churn, diffusion, history) | HEURISTIC, never decisive |

**Tier rules** — each firing rule is shown with file:line:

| Tier | Rule | Human effort (target) |
| --- | --- | --- |
| **LIGHT** | Behavior absent (IL-identical) or docs-only outside shipped projects; none of the force-DEEP triggers | Card in PR; **5% randomly re-reviewed** |
| **STANDARD** | Behavior change with direct verification evidence, localized blast radius, no force-DEEP trigger | 10–15 min |
| **DEEP** | Any force-DEEP trigger (below) | 30–45 min, high-tier owner co-signs |

**Force-DEEP triggers:** sensitive path from policy (auth, crypto, serialization *format*, unsafe, concurrency, **diagnostic/emit policy in analyzers & generators** — not every generator file); public API, wire-format or serialized-name change; cross-cutting change (fan-out above policy threshold); changes to policy, analyzer config, `NoWarn`, build/CI, dependencies, approved snapshots; ambiguous requirement; analysis UNSUPPORTED.

**Not triggers (fixed from v0.2 tier inflation):**
- Same agent wrote tests → **required check**: new tests must *fail on base and pass on head*; mutation testing on changed lines (STANDARD+).
- Intent unknown → **one decision card**, not escalation.

**Cumulative view:** tier is computed on the PR *and* on the cumulative diff per area since the last human-attested DEEP baseline, and per requirement ID / agent session (defeats splitting). Unused new code is flagged as *staged behavior*.

**Ambiguity goes up, never down.** Humans may raise a tier; lowering needs a recorded reason from the policy owner.

**Expected split (hypothesis, to measure in pilot):** LIGHT 15–25% · STANDARD 50–60% · DEEP ≤ 30%.

### [2] Verify — compute by tier

| Tier | Deterministic | AI (proposes only) |
| --- | --- | --- |
| LIGHT | re-check the IL/doc proof | none |
| STANDARD | tests + test impact; fail-on-base/pass-on-head; mutation on changed lines (time-boxed, timeout → UNSUPPORTED) | one reviewer from a **different model family than the author** |
| DEEP | + property/round-trip tests, regression corpus of past escapes | + adversarial agent; diff against independent implementation **only where one exists** (e.g. upstream PR) |

A finding is shown only with a failing test, tool fact, or cited code path. Otherwise it becomes an ABSTAINED item. Precision over recall.

### [3] Extract decisions
- **Pass 1 — blind:** extract decisions from diff + deterministic facts only, *without* PR text or agent session log (avoid adopting the agent's story).
- **Pass 2 — reconcile:** compare with the agent's stated rationale; mismatches become cards. No rationale → "intent unknown".
- Every decision must cite hunk/fact IDs; a decision citing nothing is dropped (kills invented decisions).
- Each decision: before/after behavior, alternatives, evidence + grade, traced to requirement (else **scope beyond requirement**), recommended route — **hidden until the reviewer records their own verdict** (anti-anchoring).
- Always present on STANDARD/DEEP: **"Should this change exist in this form?"**

### [4] Coverage — detecting missed decisions (deterministic)
1. **Hunk/CFG reconciliation:** every changed hunk and CFG delta (new branch, early return, catch/swallow, changed constant/default, removed call) must be claimed by a decision or a fact, or marked "mechanical consequence of Dk". Unclaimed → **"unexplained change" card**, tier +1.
2. **Scope fan-out:** compare each decision's stated scope with `SymbolFinder` reach. *2283: "fix 2 crash sites" vs 30 call sites now filtered → mismatch.*
3. **Differential behavior:** run base and head on test corpus (+ generated inputs on DEEP); each output-difference cluster must map to a decision.
4. **Changed expectations:** any changed expected value in a pre-existing test or golden file is a mandatory decision card.
5. **Extractor recall** measured offline with planted decisions — a metric, not a gate.

### [5] Brief — comprehension where the review happens
- **In the PR** (check summary + inline cards — evidence at diff time, per Google Tricorder / Meta Infer: fix rate ~0% on dashboards vs >70% at diff time).
- **HTML view** of the same ledger for STANDARD/DEEP (Thariq Shihipar: long markdown goes unread; HTML "is something I will actually read"):
  1. one-screen summary (requirement, tier + rules, counts, *not checked*)
  2. bookends: contract/type/API changes in; verification evidence out
  3. decision cards
  4. **changed subgraph only** of before/after control flow (deterministic; LLM only annotates)
  5. reading order + where to focus (file:line)
  6. primer ≤150 words if the reviewer has never touched these files (from git history)
- **Security of the view:** all repo-derived strings escaped, strict CSP, no inline script; the view never signs.
- **Off the merge path (Crux-style learning, not evidence):** a weekly audio digest of DEEP changes per area for the owning team; always prefixed "synthesized from the review ledger; not evidence." *(default pending team decision — see decisions-log)*
- **DEEP only:** instead of a quiz, one free-text box *"What could break?"* — scored afterwards against deterministic facts, used to measure reviewer attention, not to gate.

### [6] Sign
- Reviewer records a verdict per decision; **bulk-accept** allowed for items graded PROVEN/MEASURED; written reason required only for rejects and for accepting ABSTAINED/UNSUPPORTED items as residual risk.
- Signing happens **server-side** against item IDs + hashes → append-only, signed attestation (in-toto/Sigstore, OIDC identity) **and** a real GitHub/ADO approval by the same person. Required status check `decision-record` passes only for the current base+head+policy hash.
- **The person who prompted the agent cannot sign. The AI never counts toward required reviewers.**
- New commit / rebase: entries carried forward only where `git range-diff` shows the hunk unchanged and the base change does not touch blast-radius symbols; the rest returns as a delta (Iron "brain"). Re-verified in merge queue.

### [7] Learn
- Escapes, reverts **and fix-forward commits touching the same lines within N days** traced to the decision record and the tier rule.
- Escape from a LIGHT change → LIGHT paused for that area until the area owner reviews.
- Canary decisions/known bugs seeded into queues; per-reviewer catch rate tracked. Canary-verified verdicts weighted above raw dismissals (stops tired reviewers teaching the AI to go quiet).
- Reviewer AI scored like an analyzer: verified-real rate, "not useful" rate (>10% → demoted, Google Tricorder).

---

## 4. Who owns what

| Thing | Owner |
| --- | --- |
| Merge decision for a PR | Named signer (not the agent's prompter) |
| DEEP co-sign | Owner of the highest-tier path touched |
| `REVIEW_POLICY` (tiers, triggers, thresholds) | Area owners; changes are themselves DEEP |
| Reviewer AI configuration and its metrics | Platform team; demoted by data, not opinion |
| Restoring LIGHT after an escape | Area owner, recorded |

## 5. Frontend · backend · security

- **Frontend:** decision cards in the PR; HTML ledger view; verdict-first then reveal recommendation; claim → source navigation; escaped content, CSP.
- **Backend:** revision-bound jobs keyed by base+head+policy hash; artifact store; invalidation on push; failed/incomplete check = UNSUPPORTED, never pass; server-side signing; append-only attestation store.
- **Security:** repo content is untrusted data (PR text, comments, test names cannot change policy); analysis sandboxed, no secrets; session logs secret-scanned; code sent to models only within customer tenant/region; base-revision policy.

## 6. Measurement — 3-month shadow pilot, 2 teams

| Metric | Baseline | Target | Stop rule |
| --- | --- | --- | --- |
| Escapes + reverts + fix-forwards per 100 merged PRs (90-day window, by area & severity) | prior 6 months | not worse | any Sev1/2 from a LIGHT PR, or >1.5× baseline |
| Active review minutes per PR, by tier | weeks 1–2 without tool | −30% on STANDARD | +10% after week 6 |
| Decision-extraction recall (blind senior reviewer, 20 PRs/month) | — | ≥85% | <70% |
| Verified-finding precision / "not useful" rate | — | ≥70% / ≤10% | <50% for 2 weeks |
| DEEP share; median cost per PR | expected ≤30% | ≤30%; <$5 | >50% after tuning; >$15 |
| Canary catch rate per reviewer | first month | ≥80% | <60% → reviewer coaching, area LIGHT paused |

**Mini-replay (illustrative, n=4):** run triage + coverage on the four sample branches; report tier, verified findings, abstentions, minutes vs full read. Not a performance claim.

## 7. When not to trust this

- Analysis blind spots: reflection, DI, dynamic dispatch, external consumers, non-C# languages (they get no decision extraction — stated, not hidden).
- Golden/test evidence covers only its inputs; CFG facts describe control flow, not correctness.
- A wrong or incomplete requirement yields a well-evidenced wrong change.
- A polished view can persuade — verdict-first UI and canaries exist because of this.
- Extractor recall below target → STANDARD reverts to full read.

---

## 8. Worked example — `ju26-issue-2283`

| Stage | Result | Status |
| --- | --- | --- |
| Pin | base `32258fdb` (repo default branch, dependabot), head `9df83c38`, requirement #2283 | manually verified |
| Triage | **DEEP** — trigger *diagnostic policy in analyzer*: constructor wraps the single `reportDiagnostic` delegate (`TypeCollector.cs:239`) so all **30 live call sites** go through `ReportIfLocatedInCompilation` (`:1444-1450`); golden tests cover emitted code, not diagnostics | manually verified (source + grep) |
| Verify P1 | new tests `GenericsFormatterTests.cs:507-680` pass on head | **proposed → run** |
| Verify P2 | same tests fail on base with the #2283 crash (tests can fail) | **proposed → run** |
| Verify P3 | full generator suite passes → golden output unchanged for existing inputs | **proposed → run** |
| D1 | Drop diagnostics without in-compilation location — across 30 sites, not only the 2 crash sites. Alternative: upstream PR #2305 reports at `Location.None` | manually verified |
| D2 | `[0]` → `FirstOrDefault()` + new helper `GetPropertyIdentifierLocation` (`:1434`) — the crash fix | manually verified |
| D3 | README + MsgPack004 docs describe the drop policy (consequence of D1) | manually verified |
| Coverage | scope fan-out mismatch: requirement names 2 crash sites, change filters 30 | manually verified |
| Finding F1 | New helper handles only `PropertyDeclarationSyntax`, **ignoring the `ParameterSyntax` handling already present at `:926` in the base**. Positional-record property with null key: base → crash (AD0001); head → MsgPack005 silently dropped. Loud failure becomes silent loss. | ARGUED → **P4 test to run** (`MsgPack00xAnalyzerTests.cs`, `NullStringKey_PositionalRecord`) |
| A1 | Drop vs report is the maintainers' policy; #2305 unmerged, no maintainer comment | ABSTAINED |
| A2 | Generated serializer for unkeyed metadata member unchecked (tests skip generated-source check) | UNSUPPORTED |
| Decision | **Request changes:** keep D2; narrow D1 to crash sites or adopt #2305; handle `ParameterSyntax` as at `:926`; add test for positional records | to be signed by named owner |

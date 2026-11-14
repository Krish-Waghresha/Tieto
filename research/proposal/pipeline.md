> **STATUS: RESEARCH PROPOSAL — NOT FINAL.** Working draft from the research/experiment track (Jakub). Not an agreed design or implementation spec; claims marked pending/simulated/proposed are unverified.

# Decision-First Review — pipeline design (DRAFT v0.4, 2026-11-14)

> **Machines read the lines. Humans own the decisions.**
>
> Every agent-written PR is reduced to the few choices the agent made, each tied to the requirement and to a check that actually ran — or openly marked unknown. A named engineer signs exactly those choices. Any defect that escapes is traced back to the routing rule that let it through, and that area loses its right to lighter review.

**v0.4** folds in the wave A mechanisms (big tech, trading, safety-critical, visualization) using only fact-checked wording. History: v0.3 = four adversarial reviews; see [decisions-log.md](decisions-log.md). Research: [takeaways](../findings/takeaways.md), [fact-check](../findings/fact-check-waveB.md), [findings/](../findings/). Aligned with [concept-card.md](concept-card.md) v0.2.

---

## 1. Positioning — what is borrowed, what is new

| Mode | How a human gets confidence | Who does it today |
| --- | --- | --- |
| Crawl | Read every line | Classic review |
| Walk | Better diffs (semantic, stacked, refactor-aware) | difftastic, Graphite, RAID |
| Run | AI comments on the diff | Copilot, CodeRabbit, Bugbot — best ≈ 50–65% F1 depending on benchmark run (Martian; scores from secondary sources) |
| Bus | Route by risk | Cloudflare, Meta RADAR, Zalando, Rewind, Intercom, Adyen, gitStream; required in EU algo trading by MiFID II RTS 6 Art. 11(1) |
| **Plane — this concept** | PR compiled into **decisions**, each with before/after behavior and graded evidence; a deterministic coverage check shows anything no decision explains; a signed record feeds per-area trust | Not found in any product or published practice (takeaways §1) |
| Teleport — *direction, not demonstrated* | Human signs intent + invariants before code is written; merge = checked conformance + sign-off on choices beyond spec | Kiro specs, AWS Cedar point this way |

- **Borrowed (practicality):** risk routing, deterministic verdict engines, protected paths, shadow-mode rollout — all published practice in 2026.
- **New (our contribution):** (1) decisions instead of comments, (2) coverage check for missed decisions, (3) graded evidence with ABSTAINED/UNSUPPORTED as first-class outcomes, (4) signed decision record feeding per-area trust.

---

## 2. One vocabulary

| Grade | Meaning | Who may produce it | Must state |
| --- | --- | --- | --- |
| **PROVEN** | Deterministic output of a *sound or qualified* tool on the pinned SHAs | compiler, sound analyzers (e.g. Astrée/SPARK/Frama-C class), IL/API diff, exact file/byte comparisons | its known blind spots |
| **MEASURED** | An executed test/run | test runners, replay, mutation | the inputs it covers |
| **HEURISTIC** | Rule of thumb | linters, path rules, JIT risk, text search | its known false-positive rate |
| **ARGUED** | LLM interpretation citing hunk/node IDs | any model — **always ARGUED, never higher** | that it is not evidence alone |

Aviation logic (DO-330, via vendor summaries): an unqualified tool's output is verified as if a human wrote it — so a linter yields HEURISTIC at most and an LLM yields ARGUED at most.

**Outcomes** besides a finding: **ABSTAINED** (AI will not decide — why, what human action resolves it) and **UNSUPPORTED/UNKNOWN** (analysis could not run or classify — **always routed to a human**, never a pass; Adyen tags MRs low/mid/high/unknown).

**Demo status** on every artifact: *executed · manually verified · simulated · proposed.*

---

## 3. Pipeline

```
 PR + requirement ID
 [0] PIN            base/merge-base, head, policy hash, tool versions, provenance
 [1] TRIAGE         deterministic verdict engine → LIGHT / STANDARD / DEEP / UNKNOWN  (no LLM)
 [2] VERIFY         per-tier checks; AI proposes, rules index + disprove-it pass dispose
 [3] EXTRACT        decisions from diff+facts (blind), then reconcile with stated intent
 [4] COVERAGE       every hunk & CFG delta claimed by a decision or fact — else card
 [5] BRIEF          minimal card in PR + HTML view, generated from the ledger only
 [6] SIGN           named human, server-side, bound to SHAs → real PR approval
 [7] LEARN          escapes traced to rules; per-area trust; reviewer AI scored
```

### [0] Pin
- Record base (merge-base with target), head, **policy hash, analyzer-config hash, tool versions**, requirement text, author (agent/model), session log (secret-scanned).
- **Triage uses the base revision's policy and analyzer config** — a PR cannot change the rules that judge it.
- *Observed failure:* our research agent diffed `ju26-issue-2283` against the wrong base and blamed the AI for a dependabot Roslyn 4.3→4.12 bump.

### [1] Triage — deterministic verdict engine
The verdict is computed by **plain, unit-tested code** over deterministic facts (Rewind). LLM findings may be *inputs* to later stages, never the tier.

| Signal | Grade (with stated limit) |
| --- | --- |
| Build + analyzers (base config) | PROVEN under base config; HEURISTIC if PR touches config |
| Whitespace/non-doc-comment only | PROVEN — directives, `#pragma`, `#nullable`, doc comments count as changes |
| Behavior absent | PROVEN only via identical IL/metadata of every shipped assembly |
| Docs/tests paths | PROVEN path membership — *not* absence of behavior change |
| Public API diff | PROVEN for signatures — blind to wire format, diagnostic IDs, reflection, `InternalsVisibleTo` |
| Generated (golden) output | MEASURED — bounded to the generator test corpus |
| Dependencies | PROVEN direct; transitive needs lockfile diff |
| Tests removed/skipped; changed expectations | PROVEN removed/skipped; changed expected values HEURISTIC → always a decision card |
| Blast radius (`SymbolFinder`, CFG diff) | PROVEN **lower bound** (misses reflection, DI, delegates, external consumers) |
| Reused flag / newly dead code | HEURISTIC (Knight Capital pattern: a repurposed flag reached old code) |
| JIT risk (churn, diffusion, history) | HEURISTIC, never decisive |

**`REVIEW_POLICY` — every rule cites its origin** (incident, regulation or research), so a rule without a reason can be challenged (Zalando). Example rows:

| Rule | Effect | Cites |
| --- | --- | --- |
| R-PROTECTED-PATH | auth, authorization, secrets, crypto, "who can approve future changes", kill-switch / risk-limit code → DEEP, LLM cannot downgrade | Rewind protected list; RTS 6 Art. 12 (kill functionality) |
| R-DIAG-POLICY | diagnostic/emit policy in analyzers & generators → DEEP | 2283 worked example |
| R-RULES-CHANGE | policy, analyzer config, `NoWarn`, build/CI, dependencies, approved snapshots → DEEP + policy-owner sign-off | red-team review (agent edits its judge) |
| R-DEPLOY | deploy and rollback scripts/config → DEEP | Knight Capital (SEC order 34-70694: rollout missed one of eight servers; no second-person review) |
| R-CROSSCUT | fan-out above threshold → DEEP | 2283: 2 crash sites vs 28 call sites |
| R-SIZE | very large PRs → DEEP or split request (size never *lowers* a tier) | Vercel (100+ changed files always HIGH, largest monorepo); Rewind: risk "has almost nothing to do with its line count" |
| R-UNKNOWN | analysis UNSUPPORTED / unclassifiable → human | Adyen "unknown" tag |

**Tiers:**

| Tier | Rule | Human effort (target) |
| --- | --- | --- |
| **LIGHT** | Behavior absent (IL-identical) or docs-only outside shipped projects; no DEEP trigger | Card in PR; **5% randomly re-reviewed** |
| **STANDARD** | Behavior change with direct verification evidence, localized blast radius | 10–15 min |
| **DEEP** | Any force-DEEP rule | 30–45 min, highest-tier path owner co-signs |
| **UNKNOWN** | Cannot classify | Treated as DEEP until a human classifies |

**Not triggers (fixed v0.2 tier inflation):** same agent wrote tests → required check (new tests *fail on base, pass on head*; mutation on changed lines); intent unknown → one decision card.

**Cumulative drift tripwire:** tier is also computed on the cumulative diff per area since the last human-attested DEEP baseline, and per requirement / agent session. ESMA's 2026 supervisory briefing warns that a series of minor changes "could accumulate over time… into a material change." Unused new code is flagged as *staged behavior*.

**Ambiguity goes up, never down.** Lowering a tier needs a recorded reason from the policy owner. **Proportionality is itself regulation in trading:** "The depth of the review shall be proportionate to the magnitude of the proposed change" (RTS 6 Art. 11(1)).

**Expected split (hypothesis, measured in pilot):** LIGHT 15–25% · STANDARD 50–60% · DEEP ≤ 30%.

### [2] Verify — compute by tier; AI proposes, deterministic checks dispose

| Tier | Deterministic | AI (proposes only) |
| --- | --- | --- |
| LIGHT | re-check the IL/doc proof | none |
| STANDARD | tests + test impact; fail-on-base/pass-on-head; **re-run the analyzer or test that originally flagged the issue** (Uber FixrLeak: LLM fix reaches a human only after build, tests and the originating analyzer pass); mutation on changed lines (time-boxed, timeout → UNSUPPORTED) | one reviewer from a different model family than the author |
| DEEP | + property/round-trip tests; **replay** of captured inputs through base and head with output diff (Optiver replay rig, Two Sigma trace replay); regression corpus of past escapes | + adversarial agent; diff vs an independent implementation only where one exists |

Every AI finding passes three gates before a human sees it:
1. **Rules index** — the finding must map to a rule in the team's standards document; "the standards document is the sole source of truth; the model can suggest, but never define" (G-Research, 2026). Severity is set by the rule, not the model.
2. **Disprove-it pass** — a second pass tries to falsify the finding (DoorDash; design reported in secondary write-ups).
3. **Evidence** — a failing test, tool fact, or cited code path. Otherwise it becomes an ABSTAINED item. Precision over recall.

### [3] Extract decisions
- **Pass 1 — blind:** decisions from diff + deterministic facts only, without PR text or agent log.
- **Pass 2 — reconcile with stated intent** (Intercom-style intent check): compare with PR description and agent rationale; mismatches become cards; missing rationale → "intent unknown". Gong et al. (MSR 2026, 23,247 agent PRs): the most common description–code mismatch type (45.4%) is descriptions claiming unimplemented changes; high-mismatch PRs were accepted 28.3% vs 80.0%.
- Every sentence must cite a hunk or node ID; uncited claims are flagged **phantom** and dropped.
- **Decision card fields:** before/after behavior · alternatives · evidence + grade · trace to requirement (else *scope beyond requirement*) · **behavior change · reversibility · rollout safety · security** (Adyen's dimensions) · recommended route — hidden until the reviewer records their own verdict.
- Always on STANDARD/DEEP: **"Should this change exist in this form?"**

### [4] Coverage — detecting missed decisions (deterministic)
1. **Hunk/CFG reconciliation:** every changed hunk and CFG delta (new branch, early return, catch/swallow, changed constant/default, removed call) is claimed by a decision or fact, or marked "mechanical consequence of Dk". Unclaimed → **"unexplained change" card**, tier +1.
2. **Scope fan-out:** decision's stated scope vs `SymbolFinder` reach. *2283: requirement names 2 crash sites; change filters 28 call sites.*
3. **Differential behavior:** base vs head on test corpus (+ replay / generated inputs on DEEP); every output-difference cluster maps to a decision.
4. **Changed expectations:** changed expected values in pre-existing tests or golden files are mandatory cards.
5. **Extractor recall** measured offline with planted decisions — a metric, not a gate.

### [5] Brief — comprehension aid where the review happens
Visuals are pitched as **comprehension aids, not defect-detection gains**: no controlled study found that diagrams raise defect detection; decomposing changes helped understanding and cut false positives (ClusterChanges, di Biase et al. 2019).

- **In the PR — minimal card** (Microsoft Nudge-style brevity): tier + firing rules, counts of decisions/abstentions/unsupported, "what you must decide", link to the HTML view. Evidence at diff time (Meta Infer: fix rate near zero in batch → over 70% at diff time, same false-positive rate).
- **HTML view** of the same ledger for STANDARD/DEEP (Thariq Shihipar: HTML is "something I will actually read"):
  1. one-screen summary (requirement, tier + rules, counts, *not checked*)
  2. bookends: contract/type/API changes in; verification evidence out
  3. decision cards **ordered by dependency**, not alphabetically
  4. per decision: **changed subgraph + one hop, 7–12 nodes picked by PageRank** (Aider repo-map style); before/after CFG only when branch structure changed; graph built deterministically, LLM only annotates nodes
  5. one beacon line per decision (Brooks); prose explains only the *why*, never restates edges the graph shows
  6. reading order + where to focus (file:line); "usually changes with" hint from git history
  7. primer ≤150 words if the reviewer has never touched these files
- **Security of the view:** repo-derived strings escaped, strict CSP, no inline script; the view never signs.
- **Off the merge path:** weekly audio digest per area, prefixed "synthesized from the review ledger; not evidence." *(default pending team decision — see decisions-log)*
- **DEEP only:** "What could break?" free text — scored afterwards against deterministic facts, to measure attention, not to gate.

### [6] Sign — one evidence queue, every item answered
- **Single queue** (NASA JPL SCRUB: human comments and analyzer reports in one queue, the module owner responds to all of them): decisions, findings, abstentions, unsupported items, unexplained changes.
- Bulk-accept for PROVEN/MEASURED items; written reason only for rejects and for accepting ABSTAINED/UNSUPPORTED as residual risk.
- Signing **server-side** against item IDs + hashes → append-only signed attestation (in-toto/Sigstore) **and** a real GitHub/ADO approval by the same person. Required check `decision-record` passes only for the current base+head+policy hash.
- **Named approver per substantial change; author ≠ approver.** The agent's prompter cannot sign; the AI never counts toward required reviewers. Trading precedent: RTS 6 Art. 5(2) (a person designated by senior management authorises deployment or substantial update) and Art. 5(7) (record when, who made, who approved, nature of change); FCA good practice — some firms required all algorithm changes, regardless of materiality, to be approved by a senior manager.
- New commit / rebase: entries carried forward only where `git range-diff` shows the hunk unchanged; the rest returns as a delta (Iron "brain"). Re-verified in merge queue.

### [7] Learn
- Escapes, reverts and fix-forward commits on the same lines within N days traced to the decision record and the tier rule.
- Escape from a LIGHT change → LIGHT paused for that area until the area owner reviews.
- Canary decisions / known bugs seeded into queues; per-reviewer catch rate tracked; canary-verified verdicts weighted above raw dismissals.
- Reviewer AI scored like an analyzer: verified-real rate; "not useful" rate >10% → demoted (Google Tricorder's <10% effective false-positive bar).
- **Benign-PR set:** the reviewer is regularly run on known-harmless PRs to check it stays silent (DoorDash benchmark design, secondary source).
- **Periodic policy certification:** area owners re-sign `REVIEW_POLICY` on a fixed cadence (analogue of the SEC 15c3-5 annual CEO certification of risk controls).

---

## 4. Rollout and model adoption

1. **Shadow mode** — pipeline runs beside normal review, no gating (Rewind: one week shadow).
2. **Agreement gate** — go live per area only when triage tiers agree with human reviewers ≥90% (Rewind's gate; they reported ~99%).
3. **Model adoption gate** — a new reviewer model is adopted only with 100% recall on MUST/MUST NOT rules and >85% precision on the rules-index eval set (G-Research).
4. **Limited adoption** — one language (C#), narrow rule set, then widen on measured results.

## 5. Who owns what

| Thing | Owner |
| --- | --- |
| Merge decision for a PR | Named signer (not the agent's prompter) |
| DEEP co-sign | Owner of the highest-tier path touched |
| `REVIEW_POLICY` (rules, citations, thresholds) | Area owners; changes are DEEP; re-certified periodically |
| Verdict engine code and its tests | Platform team; changes reviewed as DEEP |
| Reviewer AI configuration, eval set, metrics | Platform team; demoted by data, not opinion |
| Restoring LIGHT after an escape | Area owner, recorded |

## 6. Frontend · backend · security

- **Frontend:** minimal PR card; HTML ledger view; verdict-first then reveal recommendation; claim → source navigation; escaped content, CSP.
- **Backend:** revision-bound jobs keyed by base+head+policy hash; unit-tested verdict engine; artifact store; invalidation on push; failed/incomplete check = UNSUPPORTED, never pass; server-side signing; append-only attestation store; logged, queryable verdicts.
- **Security:** repo content is untrusted (PR text, comments, test names cannot change policy); analysis sandboxed, no secrets; session logs secret-scanned; code sent to models only within customer tenant/region; base-revision policy.

## 7. Measurement — 3-month shadow pilot, 2 teams

| Metric | Baseline | Target | Stop rule |
| --- | --- | --- | --- |
| Escapes + reverts + fix-forwards per 100 merged PRs (90-day window, by area & severity) | prior 6 months | not worse | any Sev1/2 from a LIGHT PR, or >1.5× baseline |
| Active review minutes per PR, by tier | weeks 1–2 without tool | −30% on STANDARD | +10% after week 6 |
| Triage agreement with human reviewers | shadow weeks | ≥90% before go-live | <90% → area stays in shadow |
| Decision-extraction recall (blind senior reviewer, 20 PRs/month) | — | ≥85% | <70% |
| Verified-finding precision / "not useful" rate | — | ≥70% / ≤10% | <50% for 2 weeks |
| Benign-PR silence rate | — | ≥95% silent | <90% |
| DEEP share; median cost per PR | expected ≤30% | ≤30%; <$5 | >50% after tuning; >$15 |
| Canary catch rate per reviewer | first month | ≥80% | <60% → coaching, area LIGHT paused |

All targets are proposals, not results. **Mini-replay (illustrative, n=4):** triage + coverage on the four sample branches — not a performance claim.

## 8. When not to trust this

- Analysis blind spots: reflection, DI, dynamic dispatch, external consumers, non-C# languages (no decision extraction — stated, not hidden).
- Golden/test/replay evidence covers only its inputs; CFG facts describe control flow, not correctness.
- A wrong or incomplete requirement yields a well-evidenced wrong change.
- A polished view can persuade — verdict-first UI, phantom-claim flagging and canaries exist because of this.
- Extractor recall below target → STANDARD reverts to full read.
- No regulator yet defines review of AI-written code (EASA Concept Paper Issue 02 covers AI in aviation systems and operations, Levels 1–2; ESMA covers AI used in trading) — this is a proposal for that gap, not a compliance claim.

---

## 9. Worked example — `ju26-issue-2283`

| Stage | Result | Status |
| --- | --- | --- |
| Pin | base `32258fdb` (repo default branch, dependabot), head `9df83c38`, requirement #2283 | manually verified |
| Triage | **DEEP** — R-DIAG-POLICY + R-CROSSCUT: constructor wraps the single `reportDiagnostic` delegate (`TypeCollector.cs:239`) so all **28 live call sites** (27 `?.Invoke` + 1 direct call; counted by the demo bot) go through `ReportIfLocatedInCompilation` (`:1444-1450`); golden tests cover emitted code, not diagnostics | manually verified (source + grep) |
| Verify P1 | new tests `GenericsFormatterTests.cs:507-680` pass on head | proposed → run |
| Verify P2 | same tests fail on base with the #2283 crash (tests can fail; originating failure re-run) | proposed → run |
| Verify P3 | full generator suite passes → golden output unchanged for existing inputs | proposed → run |
| D1 | Drop diagnostics without in-compilation location — across 28 call sites, not only the 2 crash sites. Alternative: upstream PR #2305 reports at `Location.None`. Behavior change: yes (diagnostics silently removed) · reversible: yes · security: none | manually verified |
| D2 | `[0]` → `FirstOrDefault()` + new helper `GetPropertyIdentifierLocation` (`:1434`) — the crash fix | manually verified |
| D3 | README + MsgPack004 docs describe the drop policy (consequence of D1) | manually verified |
| Coverage | scope fan-out mismatch: requirement names 2 crash sites, change filters 28 (14×) | manually verified |
| Finding F1 | New helper handles only `PropertyDeclarationSyntax`, ignoring the `ParameterSyntax` handling already present at `:926` in the base. Positional-record property with null key: base → crash (AD0001); head → MsgPack005 silently dropped. | ARGUED → P4 test proposed (`NullStringKey_PositionalRecord`) |
| A1 | Drop vs report is the maintainers' policy; #2305 unmerged, no maintainer comment | ABSTAINED |
| A2 | Generated serializer for unkeyed metadata member unchecked (tests skip generated-source check) | UNSUPPORTED |
| Decision | **Request changes:** keep D2; narrow D1 to crash sites or adopt #2305; handle `ParameterSyntax` as at `:926`; add positional-record test | to be signed by named owner |

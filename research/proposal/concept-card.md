> **STATUS: RESEARCH PROPOSAL — NOT FINAL.** Working draft from the research/experiment track (Jakub). Not an agreed design or implementation spec; claims marked pending/simulated/proposed are unverified.

# Concept Card — Evidence-First Review

**The AI builds the case. A named human signs the verdict.**

> DRAFT v0.1 — 2026-11-14. Sources in [findings/00-landscape.md](../findings/00-landscape.md). Items marked *(pending)* are not yet verified and must not be presented as fact.

---

## The problem in one line

> *"I can have 10 Claude codes all writing code, and it doesn't matter. I'm not going to go any faster if I can't merge those PRs after reviewing them and actually deciding they work."* — Will Wilson (Antithesis), Signals and Threads ep. 26, 00:57

Agents now write code faster than humans can read it (agent tokens passed human tokens in Feb 2026; high-AI teams merge +98% PRs while review time rises +91%). The two failure modes are a review bottleneck or a rubber stamp — *"the AI said it was fine."* Today's best AI reviewers find roughly half of real bugs at roughly half precision (Martian benchmark: top F1 ≈ 50–65% depending on run, from secondary sources), so they can **advise** but cannot be the **gate**.

## Recommendation

Stop asking "did someone read every line?" and ask **"which claims about this change are proven, which are only argued, and who accepts what's left?"**

Every agent-written PR is turned into a **Review Ledger**:

1. **Obligations** — derived from the requirement ID and the diff: *what must be true for this change to be acceptable* (fixes the reported behavior, no regression in X, no new public API, no security-sensitive path touched, tests actually exercise the fix…).
2. **Evidence per obligation**, each tagged with *how* it is known — never an unexplained confidence score:

   | Tag | Meaning | Example |
   | --- | --- | --- |
   | **VERIFIED** | A deterministic tool ran on this exact revision | compiler, Roslyn analyzer, CFG/dataflow query, mutation test |
   | **TESTED** | Executable tests pass — covers only the cases tested | regression test reproducing the issue |
   | **ARGUED** | LLM interpretation with cited code locations | "this filter also suppresses diagnostic Y (TypeCollector.cs:1393)" |
   | **ABSTAINED** | The AI refuses to decide, says why and what would resolve it | "policy choice for maintainers: drop vs report" |
   | **UNSUPPORTED** | Analysis could not run or the area is out of scope | reflection, missing deps, unsupported language |

3. **Routing per obligation, not per PR** — VERIFIED and well-TESTED obligations in low-risk areas get a light check; ARGUED, ABSTAINED and UNSUPPORTED obligations, and anything in a high-scrutiny path, go to the human. **Unknown is never a pass.**
4. **A signed decision record** — the named owner records what was checked and by what, what was not and why, the residual risk accepted, and the decision (approve / request changes / reject), bound to the commit SHA.
5. **Outcome feedback** — reverts, incidents and escaped defects are traced back to the ledger; trust per code area is earned from track record and withdrawn after an escape.

## Principles

| # | Principle | Balances |
| --- | --- | --- |
| 1 | **AI advises, a named human approves.** The AI never merges, approves, or signs. | accountability |
| 2 | **Evidence over confidence.** Every claim carries its evidence tag and a link to the artifact. No percentages nobody can explain. | confidence, transparency |
| 3 | **No self-certification.** The authoring agent's summary and its own tests are *inputs*, not evidence. Tests are checked independently (deleted/weakened tests flagged; mutation testing on high-risk paths). (Optiver, Jane Street) | hallucination, quality |
| 4 | **Abstention is a feature.** The reviewer must say what it did not decide. A ledger with zero abstentions on a non-trivial change is itself suspicious. | hallucination, risk |
| 5 | **Depth follows risk, not size.** Each path has an owner and a scrutiny tier (Jane Street Iron, Cloudflare). A one-line auth change gets a full read; a 200-line doc change may not. | risk, cost |
| 6 | **Deterministic first, LLM second.** Tools discharge what they can; the LLM explains what remains and proposes findings that must be verified before posting. Precision over recall. | quality, noise |
| 7 | **Evidence expires.** A new commit invalidates the ledger for affected obligations. | correctness |
| 8 | **Repo content is untrusted input.** PR text, code comments and docs cannot change review policy; analysis runs sandboxed without secrets. | security |
| 9 | **Trust is per area, earned and withdrawn.** Lighter review is a privilege granted from track record and revoked after an escape. | risk, scale |

## Review mechanics — borrowed from Jane Street's Iron

Jane Street has run mandatory, ownership-based review for 10+ years and in 2026 named the problem directly: *"the whole existence of AI agents has kind of broken the social contract around code review… now all you need is a prompt and a dream and you can for free create a plausible looking problem. But it's still hard work to verify that it makes sense."* (Ron Minsky, Signals and Threads ep. 31, 01:43:33). We adapt their mechanics to a GitHub-style flow:

| Mechanic | Iron (Jane Street) | Evidence-First Review |
| --- | --- | --- |
| **Ownership + tier in the repo** | Each file declares owner and "scrutiny" (required reviewers, n of k) | `REVIEW_POLICY` file per path: owner, risk tier, required ladder rung, human quorum. AI may count toward *k*, never as the required human |
| **Escalation resets approval** | Raising scrutiny forces re-review from scratch | Raising a path's tier, or a change touching a higher-tier path, invalidates prior light-route decisions |
| **Attestation "brain"** | Per person/branch record of exactly what they read; "you never have to read a commit twice" | Decision record stores exactly which obligations and hunks the human attested. After an agent amends code, the human sees only the delta; **an approval never covers code nobody attested** |
| **Seconder** | A named co-designer explicitly signs off before file reviewers | Order: deterministic checks → AI first pass → **named human seconder** → owners of high-tier paths. The AI is never the seconder |
| **CRs live in the code** | Review comments must be resolved or reassigned before release | Every AI finding and abstention needs a human resolution: *fixed / rejected with reason / deferred to owner*. Overrides become the audit trail and the training signal for the reviewer |
| **Hard release gate** | "If you haven't fully reviewed a branch, you can't release it." | Merge is blocked by tooling — not policy text — while obligations are unresolved or evidence is stale |
| **Evaluate the reviewer** | AI review model replied "I'll do it tomorrow" — imitating humans ≠ doing the task; graders checked by "meta graders" | The AI reviewer is scored on held-out known bugs and on escapes, not on how human it sounds; gaming of the gate is a monitored risk |
| **Merit, not only correctness** | AI PRs treated as prototypes; "too many knobs" | One obligation always routed to the human: *should this change exist in this form?* |

What does **not** transfer: OCaml's type system doing much of the verification for free, a custom monorepo review tool, and a firm that pays for heavy review culture. A GitHub/Azure DevOps flow needs bots and branch protection to approximate this — hence the reference implementation is a concept, not a product.

## Verification ladder — what evidence each risk tier requires

Each path has a scrutiny tier. Higher tiers must climb further before an obligation counts as discharged. Whatever the ladder does not discharge goes to the named human — **plus the spec itself**, since a proof against the wrong requirement proves nothing.

| Rung | Evidence | Required from | Lesson behind it |
| --- | --- | --- | --- |
| 1 | Compiler, warnings-as-errors | all tiers (gate) | zero false positives at build time (Google) |
| 2 | Analyzers (Roslyn, banned-API rules, nullable) | all tiers | rule with >10% "not useful" is demoted to advisory (Google Tricorder) |
| 3 | Existing tests + golden generated-output diff, explained by the LLM | Tier 1 (low) + | show *exactly* what changed in emitted code |
| 4 | CFG / dataflow facts on changed methods (new paths, new reads, reachability) | Tier 2 + | discharge specific obligations mechanically, at diff time (Meta Infer: fix rate ~0% batch → >70% diff time) |
| 5 | Mutation + property / round-trip tests | Tier 2 + — **mandatory when the same agent wrote code and tests** | tests must be shown able to fail (Meta ACH, Optiver) |
| 6 | Model checking (TLA+, P, Coyote) | Tier 3: concurrency, protocols, distributed state | AWS, Datadog, MongoDB |
| 7 | Proof on a model + differential testing against real code | Tier 4: crypto, authorization, safety-critical | AWS Cedar, seL4 cost ≈ 25 person-years |

**Delivery rules:** evidence appears in the PR at diff time (not on a dashboard nobody visits — Google, Meta); a finding that cannot be verified is not posted; the reviewer's own "not useful" rate is tracked like any analyzer.

## Worked example (to be completed)

**Requirement:** MessagePack-CSharp issue #2283 — source generator and analyzer crash (`IndexOutOfRangeException`) on closed generic value types from referenced assemblies, leaving AOT apps without a resolver.
**Change:** branch `ju26-issue-2283`, commit `9df83c38`, ~29 lines in `TypeCollector.cs` + 189 lines of tests.

| Obligation | Tag | Evidence | Route |
| --- | --- | --- | --- |
| Crash no longer occurs on the reported shape | TESTED *(pending run)* | New metadata-reference tests `GenericsFormatterTests.cs:507-680` | light |
| No other diagnostics silently lost | ARGUED → finding *(pending verification)* | New filter `ReportIfLocatedInCompilation` (`TypeCollector.cs:239, 1444-1450`) wraps *all* diagnostics; positional-record properties get `Location.None` and are dropped | **human** |
| Diagnostic policy for metadata types (drop vs report at `Location.None`) | **ABSTAINED** | Agent drops; upstream PR #2305 reports. Maintainer policy; no authoritative answer | **human** |
| Generated serializer correct for unkeyed metadata member | **UNSUPPORTED** | Tests skip generated-source check; needs build + round-trip | **human** |
| No public API change | VERIFIED *(pending tool run)* | API diff | light |

**Expected outcome:** *Request changes* — the AI's finding and abstention give the owner a concrete, checkable reason, without reading all 218 lines.

## Trade-offs

- **Less reading vs missed defects** — light routing will let some defects through; we measure escapes and withdraw trust instead of pretending otherwise.
- **Accessible explanations vs lost nuance** — ARGUED claims can be persuasive and wrong; they are labeled, cite code, and never discharge an obligation alone.
- **Deeper analysis vs latency/cost** — model checking and proofs only for top-tier paths; most PRs stop at compiler + analyzers + tests.
- **More abstentions vs more human load** — a reviewer that abstains too much is useless, too little is dangerous; abstention rate is a tracked metric.

## Limits — when not to trust this

- Analysis cannot see reflection, dynamic dispatch, generated code it did not run, missing dependencies, or unsupported languages → tagged UNSUPPORTED, routed to humans.
- Passing tests prove only tested cases; CFGs describe control flow, not correctness. Neither proves the change right.
- Incomplete or wrong requirements produce well-evidenced wrong changes. The ledger is only as good as the requirement.
- Same-model review shares blind spots; use different models / deterministic checks for independence.
- A polished ledger can create false reassurance — spot-checks of light-routed changes are mandatory.

## How trust is measured

| Metric | Why | Target direction |
| --- | --- | --- |
| Reverts, incidents, escaped defects per area (with denominators) | Safety must not drop | flat or down |
| Active human review time vs time to merge (separately) | Efficiency | down |
| Share of obligations routed to humans + routing reasons | Where attention goes | explained, stable |
| AI findings verified real / accepted by reviewer (separately) | Reviewer precision | up |
| Abstention rate and how abstentions were resolved | Calibration | stable, justified |
| Spot-check false negatives on light-routed changes | Reviewer recall | down |

**Stop rule:** a critical escape from a light-routed change pauses light review for that area; the area owner investigates and restores eligibility.

**Rollout:** one language (C#), narrow check set → shadow mode alongside normal review → limited adoption only after measured results.

## Who owns the decision

The **named engineer** who signs the decision record. Not the agent that wrote the code, not the AI reviewer, not "the process." The record states exactly what they relied on and what risk they accepted.

## Why this isn't already solved

Routing (CodeRabbit, gitStream, Cloudflare), ticket traceability (Qodo, Baz, Aviator) and deterministic-vs-AI separation (Semgrep) exist separately. **No product produces an abstention record, a signed decision record, or tracks the reviewer's misses to earn and withdraw per-area trust.** Evidence-First Review is an accountability layer *over* existing reviewers and analyzers, not another reviewer competing on F1.

> **STATUS: RESEARCH FINDINGS — NOT FINAL.** Synthesis of all research waves (2026-11-14). Numbers are only as good as their source — check [fact-check-waveB.md](fact-check-waveB.md) before putting any on a slide.

# Takeaways — what Decision-First Review should take from existing companies and products

## 1. The honest positioning (changed by wave A)

**Three-tier risk routing is no longer novel.** In 2026 at least Zalando, Rewind, Intercom, Adyen and Vercel published LIGHT/STANDARD/DEEP-style PR triage, and Cloudflare, Meta (RADAR) and Jane Street (Iron scrutiny) have equivalents. Regulation even mandates it for trading: MiFID II RTS 6 Art. 11(1) — *"The depth of the review shall be proportionate to the magnitude of the proposed change."*

→ Routing is our **practicality** argument (it is proven practice), not our **novelty**.

**What nobody publishes — our contribution:**
1. **Decisions, not comments** — the PR compiled into the few choices the agent made, each with before/after behavior, evidence grade, alternatives, and trace to requirement.
2. **Coverage check for missed decisions** — every changed hunk and control-flow delta must be claimed by a decision or a fact; unclaimed changes surface automatically.
3. **Graded evidence ladder** — PROVEN (with stated blind spots) / MEASURED / HEURISTIC / ARGUED, plus ABSTAINED and UNSUPPORTED as first-class outcomes.
4. **Signed decision record that feeds trust back per area** — escapes revoke lighter review for that area.

## 2. What to take, by source

| From | Mechanism | Where it lands in the proposal |
| --- | --- | --- |
| **Rewind** | Deterministic, unit-tested verdict engine; LLM findings are inputs, never the verdict; protected always-human paths; shadow week → ≥90% agreement gate | [1] Triage + rollout |
| **Zalando** | Each triage rule traced to the incident that motivated it | REVIEW_POLICY: every rule cites its incident |
| **Adyen** | Dimensions: behavior change, reversibility, rollout safety, security; **UNKNOWN** tier defaults to human; service graph for blast radius | Decision card fields; UNSUPPORTED → human |
| **Intercom** | Sub-agent checks diff vs stated intent; validated with auditors (Schellman; SOC 2, ISO 42001 listed — no published control mapping) | [3] reconcile pass; compliance slide |
| **Uber FixrLeak** | LLM fix reaches human only after build + tests + **re-running the analyzer that flagged the issue** | [2] Verify ladder |
| **Uber uReview** | Confidence thresholds per assistant × language × comment category; suppress low-value categories | Reviewer AI tuning; Tricorder-style demotion |
| **Uber Piranha** | Auto-generated cleanup diff routed to the flag's owner | Sign-off routed to path owner |
| **DoorDash** | "Disprove-it" pass tries to falsify each finding; benchmark includes benign PRs to test silence | [2] finding verification; reviewer eval set |
| **G-Research** | LLM findings validated against a rules index; "the model can suggest, but never define"; 100% recall on MUST rules + >85% precision before adopting a model | Model adoption gate |
| **Cloudflare** | Tiers by risk, auth/crypto always full; "break glass" override logged (0.6%) | Override path + metric |
| **Google Tricorder** | <10% effective false positives or the check is disabled; show at diff time | Reviewer AI demotion rule; cards in PR |
| **Meta Infer** | Same analysis, diff-time vs batch: fix rate ~0% → >70% | Evidence lives in the PR, not a dashboard |
| **Jane Street Iron** | Per-path owner + scrutiny; reviewer "brain" (only see the delta); hard release gate; AI reviewer that learned "I'll do it tomorrow" | [6] Sign, delta re-review; evaluate reviewer on outcomes |
| **Optiver** | No agent self-certification; captured-traffic tests as completion criteria | Fail-on-base / pass-on-head; replay evidence |
| **Optiver / Two Sigma** | Replay captured production traffic through old and new builds; diff outputs | [4] differential behavior check |
| **Knight Capital (SEC order)** | No second-person review, no written deploy procedure, reused dead flag | Dead-code / reused-flag detector; deploy & rollback are reviewable |
| **MiFID II RTS 6 / ESMA / FCA** | Named approver per substantial change; records of who/what/when; cumulative effect of small changes; define "material change" | Force-DEEP triggers written as policy; cumulative drift tripwire |
| **SEC 15c3-5** | Annual CEO certification of risk controls | Periodic sign-off of the triage policy itself |
| **Airbus / DO-333** | Formal proof replaced unit testing where proof possible; only **qualified** tools earn credit | Only sound/qualified tools may yield PROVEN; linters ≤ HEURISTIC |
| **DO-178C / DO-330** | Unqualified tool → output verified as if human-written; independence by assurance level | LLM output is always ARGUED; author ≠ signer |
| **SCADE (qualified codegen)** | Trusted generator → reduced code-level verification | Provenance: output of a vetted generator can be LIGHT |
| **NASA JPL SCRUB** | Human comments + analyzer findings in one queue; every item needs a response; closeout | The evidence ledger + mandatory resolution |
| **Gong et al. MSR 2026** | among description–code mismatch types in 23,247 agent PRs, 45.4% are descriptions claiming unimplemented changes; high-mismatch PRs (1.7%) accepted 28.3% vs 80.0% | Blind extraction; every sentence cites a node/line; HalluJudge-style check |
| **ClusterChanges / di Biase** | Decomposing a change helps understanding, cuts false positives; no proven defect-detection gain | Pitch visuals as comprehension, not bug-finding |
| **Aider repo map / Roslyn** | PageRank to pick 7–12 nodes; changed subgraph + one hop | Flow graph spec |
| **Thariq Shihipar (Anthropic)** | HTML instead of markdown for long agent output; one-screen rule; "bookends" (types in, verification out) | HTML ledger view; summary first |
| **Crux** | Verified comprehension per person per commit, expires on code change | Reviewer primer; record expires with SHA |

## 3. What NOT to claim

- That routing itself is new (it isn't).
- That diagrams increase defect detection (no controlled evidence found).
- That an LLM can be a qualified tool (no regulator accepts that; DO-178C would treat its output as unverified).
- Any metric from our own demo as performance evidence (n=1, scripted).

## 4. Regulatory gap we sit in

- ESMA (2026) requires firms to recognise AI used *in trading*, but says nothing about AI *writing* trading code.
- EASA (Concept Paper Issue 02, Levels 1–2) and FAA AI guidance cover AI *in* aviation systems and operations, not AI *writing* aviation software.
- EU AI Act treats coding assistants as generally not high-risk.
→ No regulator yet defines how AI-written code is reviewed. Regulated customers (Tieto's banks, healthcare, public sector) will need a defensible answer: **named approver, proportionate review depth, records of what was checked, independence of author and approver.** That is exactly the decision record.

## 5. Slide-ready quotes (verify in fact-check before use)

1. "The depth of the review shall be proportionate to the magnitude of the proposed change." — MiFID II RTS 6, Art. 11(1)
2. "Knight did not have a second technician review this deployment." — SEC Order 34-70694 (2013)
3. "The model can suggest, but never define." — G-Research (2026)
4. "A PR's risk has almost nothing to do with its line count." — Rewind (2026)
5. "…AI agents has kind of broken the social contract around code review." — Ron Minsky, Jane Street (2026)
6. "The same program analysis, with same false positive rate, had much greater impact when deployed at diff time." — Meta, CACM 2019

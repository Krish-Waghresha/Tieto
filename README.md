# Decision-First Review — end-to-end demo (NOT FINAL)

> **STATUS: DEMO / REFERENCE IMPLEMENTATION — NOT A PRODUCT, NOT FINAL.** Research-track experiment for the Tieto "Earned Trust in AI Code" challenge (Junction 2026). Design and findings: branch `research/findings` → `research/`.

**Machines read the lines. Humans own the decisions.** The bot reduces an agent-written PR to the few choices the agent made, each tied to the requirement and to a check that actually ran — or openly marked unknown. A named engineer signs exactly those choices.

## The real case

- **Requirement:** [MP-2283](requirements/MP-2283.md) — MessagePack-CSharp issue #2283 (generator/analyzer crash on closed generic value types from a referenced assembly).
- **Agent change:** the challenge's branch `ju26-issue-2283` (commit `9df83c38`) of `te-industry-tech-office/junction26-messagepack-csharp`, reproduced as PR **`demo/agent-2283` → `demo/base`** in this repo. Files under `sample/` are verbatim copies (MIT, see `sample/LICENSE`); proof P0 checks byte-identity in CI (verified locally by sha256 during setup).

## What happens on the PR

| Stage | What | How it is known |
| --- | --- | --- |
| Pin | base/head SHAs, policy hash, upstream SHAs, requirement hash | recorded in the ledger |
| Triage | `review-policy.json` rules → LIGHT / STANDARD / DEEP; every rule cites the incident or regulation behind it | plain, unit-tested code (`reviewbot/triage.py`); **base-revision** bot and policy |
| Facts | fan-out of changed delegates, branch shape of new methods, requirement anchors, precedent checks | deterministic text-level parse (graded HEURISTIC/PROVEN; Roslyn proposed) |
| Proofs | P0 provenance · P1 new tests pass on head · P2 same tests fail on base · P3 whole generator suite on head · P4 probe for finding F1 on base and head | **designed to execute** in GitHub Actions on the upstream repo (`ci/run_proofs.sh`). **Current status: not executed** — Actions is not enabled on this repo yet |
| Decisions | D1–D4, finding F1, abstentions A1–A2 | **SIMULATED** extractor output (`demo/MP-2283/review-input.json`) — stand-in for an LLM pass; every claim must cite hunk/fact/proof IDs and numbers are filled from facts |
| Coverage | every changed hunk must be explained; scope fan-out check | deterministic |
| Brief | sticky PR comment (one screen) + single-file HTML report (graph, cards, evidence, quiz, audio, sign) | rendered from the ledger only |
| Sign | reviewer submits a **PR review** whose body is the `/sign` text | `decision-sign` workflow validates head SHA, ledger, every item resolved, review state matches, signer ≠ PR author; sets `decision-record` status |

## The review UI (branch `demo/ui`)

A 7-step guided review built with React 19 + React Flow + Shiki, compiled to **one self-contained HTML file** (`reviewbot/static/review-app.template.html`, ~950 KB). The bot injects the ledger (and an optional narrated briefing) and a hash-only CSP — CI needs no Node.

1. **Verdict** — tier, owner, plain-language read, checks run, scope meter (2 needed vs 28 affected), evidence ladder, ≤75 s audio briefing
2. **What changed** — before/after flow graph built from tool facts; the dropped path is the only accent; click a box for its code
3. **Decisions** — before/after cards; **your verdict first**, the AI's suggestion unlocks after (reduces over-reliance)
4. **Found / won't decide** — F1 with its tool facts and the tests that try to disprove it; A1/A2
5. **Evidence & gaps** — filter by grade; checks, tool facts, every changed block, what was not checked
6. **Quick check** — 3 questions keyed by tool facts/tests, never a gate
7. **Sign** — you vs AI, residual risk, generates the `/sign` review text (validated by the same rules as the bot)

Deep links: `report.html#step-3`. Keys: ← →. "Full page" mode shows all steps. Rebuild the UI: `cd ui && npm ci && npm run build`.

## Try it

1. Open the PR, read the sticky comment, click **full report** (opens the HTML in the browser; repo login required).
2. In the report: give a verdict per card (the bot's recommendation is revealed after), answer the 3 questions, press **Generate /sign text**.
3. On the PR: **Files changed → Review changes**, paste the text, submit as **Request changes** or **Approve** (must match the text). The PR author cannot sign — separation of duties.

Local run (no .NET needed; proofs show as *not executed*):

```bash
python3 -m unittest tests/test_reviewbot.py
python3 -m reviewbot review --base demo/base --head demo/agent-2283 --out out --evidence evidence
open out/report.html
```

## Honest labels

- **Executed:** triage, tool facts, coverage, unit tests (41). Proofs P0–P4 are wired but **not yet executed** (Actions disabled on this repo).
- **Simulated:** decision extraction text (no model connected); graph layout is hand-designed around deterministic facts.
- **Proposed, not built:** Roslyn-based facts, Sigstore/in-toto signing, mutation testing, cross-model reviewer, per-area trust tracking, canaries.
- **Security model:** the review runs on `pull_request_target` from the **base** branch (workflow, bot, policy, proof script, pinned SHAs); PR files are read as data only; proofs run with a read-only token. Triage diffs the whole repo, so changes to `.github/**`, `reviewbot/**` or `review-policy.json` force a deep review.
- **Known limitation:** the `/sign` workflow uses `pull_request_review`, which GitHub runs from the PR merge ref — a malicious same-repo PR could alter it. Production: GitHub App or default-branch `workflow_run`, plus a ruleset protecting the pipeline files.
- **Other limits:** text-level C# parsing; one sample change.

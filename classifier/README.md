# Classification References

Two C# source snapshots -> Roslyn method graph and facts -> attention policy -> one colored change map.

This is a synthetic classifier prototype with a local GitHub PR watcher. It does not reuse the earlier MessagePack classification or report UI.

## Evidence-v2: Bulk Invoice Import

The invoice example demonstrates evidence-supported confidence in **substantive new behavior**, not change complexity or whitespace equivalence. [Invoice PR #3](https://github.com/Krish-Waghresha/earned-review-demo/pull/3) links to its interactive review. The older order-flow PR remains separate.

```sh
npm run demo:invoice
```

To build and open the invoice playground locally from this directory:

```sh
npm ci
npm run demo:invoice
node web/build.mjs out/invoice-import/analysis.json out/invoice-import/preview.html
open out/invoice-import/preview.html
```

Requires Python 3 and .NET 8. On platforms without `open`, open the generated HTML in your browser. To verify it, install Chromium with `npx playwright install chromium` and run `node web/check-invoice.mjs`. To create or update the private GitHub PR and its locally served review link, use `python3 github_demo.py --invoice` with an authenticated `gh` CLI, then keep `npm run playground:serve` running. That publication command writes to GitHub; the local build above does not.

The command runs real Roslyn PA and a trusted, local .NET fixture, then applies the evidence-v2 classification contract to explicitly authored AI judgments. No model is called, no PR is published, and no arbitrary PR code is executed. The runner executes only the developer-authored synthetic invoice project in this repository.

- **Diff:** 1,618 added production/test lines in 15 files; 834 production lines and 784 test lines. No generated artifacts, whitespace-only edits, or lockfile padding are counted.
- **Methods:** 17 green, 6 amber, 1 red, 1 gray. Five of ten feature modules are entirely green; the composed importer and preview inherit dependency attention.
- **Checks:** 87 pass and one deliberately fails. `retry.lost-acknowledgement` expects one persisted invoice but observes two because each retry allocates a new ID. The runner refuses unexpected failures or a silently disappearing counterexample.
- **Green:** CSV parsing, normalization, validation, reconciliation, and structured reporting have supporting PA facts, requirement-linked executed checks, and authored compliance judgments above the illustrative threshold.
- **Amber:** cancelled-invoice duplicate handling needs a business decision; callers of this policy or the risky writer/provider also need attention.
- **Red:** the executed lost-acknowledgement scenario exposes duplicate persistence.
- **Gray:** the tax provider's dynamic target and production contract remain unavailable despite passing stub tests.

Outputs under `out/invoice-import/`: `change.patch`, `diff-stat.json`, `pa.json`, `evidence.json`, expanded `judgments.json`, `analysis.json`, `summary.json`, and `review.md`. Start with `review.md` and inspect the source/evidence JSON when needed. The baseline is `fixtures/invoice-import/base/`; the head overlays `head/` onto that baseline and adds `tests/`. Requirements and authored judgments are adjacent JSON files.

Authored judgments are bound to exact source, requirement, and test-source hashes. Changes require re-reviewing the fixture and explicitly updating those bindings; `python3 invoice_demo.py --prepare` prints candidate bindings without classifying. Test associations are declared at module scope, **not measured line or branch coverage**. Public declarations are explicitly included in those module judgments. Test source is executed and included in the diff but is not itself AI-reviewed. Green is a bounded review recommendation, never proof or merge authorization. Confidence numbers and the 0.90 threshold are illustrative and uncalibrated; there is no public benchmark result or measured review-time saving.

Lessons from this iteration: a larger fixture exposed `nameof(...)` being mistaken for a runtime call, now fixed using Roslyn's operation type; negative sub-cent amounts must be rejected before rounding; a retry test must include failure after commit, not just before it. The legacy order-flow policy below remains unchanged for reproducibility.

## GitHub-native demo

[Synthetic PR #2](https://github.com/Krish-Waghresha/earned-review-demo/pull/2) now has [one colored graph comment](https://github.com/Krish-Waghresha/earned-review-demo/pull/2#issuecomment-6877551116) and two inline attention comments. The repository stays private. The older MessagePack PR is unchanged.

```sh
npm run github:watch
```

The watcher polls `synthetic/base` <- `synthetic/order-pricing` every 15 seconds. It fetches source blobs at the actual base/head SHAs, runs Roslyn and the local classification policy, and posts one Mermaid graph with a one-line legend and collapsed reasons. Only red or unresolved changed methods receive inline comments. It never approves or merges.

Run `npm run playground:serve` in a second terminal to enable the comment's **Open interactive playground** link. It serves only generated playground files at `http://127.0.0.1:5174`; each link identifies its PR and analysis result. This is a local demo, so the server must run on the machine opening the link. No public deployment is created. For shared hosting, serve the generated `out/playground/` directory and set `EARNED_PLAYGROUND_URL` to that HTTP(S) base URL before publishing; the setting alone does not upload files. Generated HTML includes reviewed source, so keep hosting access appropriate for the private repository.

```sh
npm run github:review -- --pr 2
npm run github:review -- --pr 2 --publish
npm run test:mermaid
```

Without `--publish`, review writes a local preview under `out/pr-2/` and a self-contained playground under `out/playground/`. Repeated publication of unchanged source/policy does not add duplicate graphs or annotations. Presentation updates reuse unchanged inline findings on the same commit. New revisions invalidate the previous graph before analysis; base/head are rechecked before publishing. Old inline comments remain revision-bound history. The local Mermaid check verifies syntax, nodes, edges, and darker color fills; GitHub uses its own renderer/theme.

For a fresh recording, close PR #2 without merging or deleting its branches, then run `npm run github:prepare`. That command reuses the dedicated synthetic branches and opens a new PR. Keep exactly one watcher running; stop it with Ctrl+C when finished. It posts as the authenticated `gh` CLI account, not a separately installed GitHub App.

Requirements and source come from the pinned snapshots; the local policy and analyzer are trusted. No PR project files or code are executed. Inputs are limited to 30 changed files, 50 repository files, and 2 MB of UTF-8 text. Unsupported inputs are refused rather than classified green. Only transient read requests retry; writes are not blindly retried.

## Run

From this directory:

```sh
npm ci
npm run demo
open out/graph.html
```

Requires Python 3, a .NET 8-compatible SDK, and Node.js. This machine uses the existing SDK under `~/.local/share/teito-tooling/dotnet`; elsewhere set `DOTNET_PATH` or put `dotnet` on PATH. The analyzer pins Roslyn 4.12.0.

The graph is self-contained and needs no server. Select a block for its diff, one-sentence reason, rule, and compiler facts. Arrows are call dependencies, not a claim that all calls execute in that order. Solid/dashed edge styles distinguish unchanged and added/removed relationships; node colors mean human attention only.

## Red Block Review

`Access.CanSubmit` offers **Understand**, source inspection, and a local concern. The understanding view compares the before/after authorization checks, including short-circuiting, for all four combinations of active user and matching tenant. Outcomes are an illustrative model of the pinned sample, not execution of the PR. The optional quiz, narration, and transcript come from `fixtures/order-flow/access-review.json`.

On macOS the build uses `say` with Samantha to generate a narration WAV, cached by transcript hash under ignored `out/audio/` and embedded in the HTML. Other platforms retain the transcript without audio. Playback stops when the explanation closes. Reviewer name, note, self-reported understanding confidence, and the submitted quiz answer can be saved locally and exported as `access-review-note.json`. That record remains red with `approved: false`; neither quiz success nor confidence clears the warning. This is not a GitHub review submission or a full-PR sign-off. The original **Export analysis** remains unchanged.

## Synthetic Advantage, Used Honestly

The fixture contains four independent changes in an order workflow:

| Change | What the engine observes |
| --- | --- |
| Receipt formatting | Only whitespace changes; token content, method signature, and resolved calls match |
| Bulk pricing | New conditional behavior and arithmetic |
| Authorization | Behavior changes on a method marked as a review boundary in the base snapshot |
| Shipping integration | A new dynamic call whose runtime target cannot be resolved |

Expected colors live in `fixtures/order-flow/oracle.json`. The classifier never reads that file. It is used only after analysis by tests or the evaluation command. These examples were designed to exercise the policy, so agreement is not independent evidence of general reliability.

Additional source-level tests change whitespace inside a string, add a preprocessor directive, and rename the authorization class without changing its meaning. Policy tests exercise removed boundary markers, model disagreement, incomplete analysis, and changed callees.

## What Is Real

- Roslyn parses and semantically compiles both snapshots, without executing their code.
- Method identities, source calls, unresolved targets, CFG blocks, branch conditions, and region data-flow facts come from Roslyn.
- A versioned local policy assigns colors. Changes outside analyzed methods get gray file nodes rather than disappearing.
- Unchanged one-hop call context is shown as outlined blocks. Dynamic targets are explicitly unknown.
- Green is restricted to a whitespace-only method contract with complete analysis, stable signatures/calls, no directive or caller-source sensitivity, no unscoped file/declaration change, and no non-green changed callee. It is not a blanket behavior-equivalence proof or merge permission.
- The boundary marker's attribute name comes from the trusted local policy. This v1 does not automatically discover every security-sensitive method.

## Model Adapter

The optional Gemini Decision adapter sends the requirement, changed code, and compiler facts to Google's Decisions API. Model input is treated as untrusted data. Its distributions must validate before use; model signals can escalate attention but cannot downgrade protected or unknown PA results.

Configure `GEMINI_API_KEY` or `GOOGLE_API_KEY` directly in your terminal environment, never in browser code or committed files, then:

```sh
npm run classify:hybrid
npm run build
```

No key is configured on this machine at implementation time. The exercised run is **PA-only**. The adapter is implemented and tested with controlled responses, but a live provider call, access entitlement, latency, and model quality have not been verified. No responses were fabricated. Gemini Decision is the candidate identified in Google's November 2026 documentation, not a user-confirmed model selection.

The model's 0.85 escalation threshold is a prototype policy parameter, not calibrated on code review. There is no separate generative LLM adjudication pass, learned risk calibrator, or model training in v1. This is not yet an evaluated PA + ML + LLM system.

## Verification

```sh
npm run test:engine
npm run evaluate:synthetic
npx playwright install chromium
npm run test:browser
```

The evaluation command measures agreement, false-green predictions, gray/abstention share, and the fraction offered lighter review. No green predictions produces an undefined false-green fraction, not a misleading zero-risk claim.

Public evaluation data and a human-attention labeling rubric are still to be selected. Keep held-out repositories separate from prompt/policy tuning. A code-fixing benchmark such as SWE-bench does not directly validate these attention labels. Future comparison should report PA-only, model-only, and hybrid results, with denominators and false-green costs. No public benchmark, review-time saving, or production safety number is claimed here.

Playwright checks generated node colors, source details, zoom, real JSON export, no external requests, CSP, and desktop/mobile layouts. Test artifacts are under ignored `test-results/`.

## Legacy Order-Flow Scope

Source-only C# 12 analysis against the analyzer's .NET 8 runtime references. No MSBuild/project configuration loading, source generators, custom analyzers, deployment or runtime tests. Dependency/reflection resolution is incomplete by design. Every changed block is represented or marked outside scope, but this is not proof of semantic completeness.

Base/head labels in the standalone map are source-snapshot hashes. GitHub results additionally record the actual PR base/head commits. The synthetic branches and PR were created in the existing private demo repository; no approval, merge, or existing worktree replacement occurred.

The legacy order-flow result is PA-only; the invoice reference uses evidence-v2 with authored AI judgments. The optional live provider adapter is still Gemini-only; an OpenAI or NVIDIA adapter must be wired before those keys can be used. Keep all keys in the local environment, never in PR comments, source, or browser assets.
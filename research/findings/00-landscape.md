> **STATUS: RESEARCH FINDINGS — NOT FINAL.** Collected from web sources and read-only inspection on 2026-11-14. Vendor claims and [UNVERIFIED] items must be checked before use on slides.

# Research: Earned Trust in AI Code (Tieto, Junction 2026)

Compiled 2026-11-14 from web research and read-only inspection of the sample repo.
Labels: **[vendor]** = self-reported by a vendor; **[UNVERIFIED]** = secondary source only, check before quoting; **[read]** = verified by reading source; **[inferred]** = reasoning from code, not executed.

---

## 1. Tieto — who we are pitching to

- **Company:** Tietoevry rebranded to **Tieto** (2025). Units: **Tieto Banktech**, **Tieto Caretech**, **Tieto Indtech**, **Tieto Tech Consulting**. Infra business spun out as Vivicta (Sept 2025, secondary source). ~14k employees, 2025 revenue EUR 1,852M (−1%), EUR 115M cost programme. CEO Endre Rangnes.
  - Annual report 2025: https://www.tietoevry.com/siteassets/images--videos/06-investor-relations/2026/agm/tieto_annual_report_2025.pdf
  - Leadership changes: https://www.inderes.fi/releases/tieto-appoints-juuso-pajunen-as-chief-financial-officer-johan-enger-nygaard-and-bent-phillips-to-continue-leading-tech-consulting-and-indtech-businesses
- **Challenge owner (likely):** GitHub org `te-industry-tech-office` — probably the Indtech tech office (inference; no public page). Only public repo is the challenge copy of MessagePack-CSharp (created 2026-11-11).
- **AI dev stance:**
  - Tech Consulting promotes "AI-augmented software engineering" (GitHub Copilot + custom agents across analysis → plan → implement → test → docs); telecom R&D claims ~50% lead-time reduction "while maintaining telecom-grade quality". Key line: *"Developers review analyses, plans, implementations, and merge requests. Generated code uses the established release gates."* [UNVERIFIED, staff LinkedIn]
  - Care R&D: ~23% productivity gain from Copilot (Nov 2024): https://news.cision.com/tieto/r/generative-ai-helps-to-drive-23--increase-in-r-d-productivity-at-tietoevry-care,c4065927
  - Microsoft Copilot specialization (Jul 2026, secondary): https://www.leadersnet.at/news/101517,tieto-erreicht-microsoft-copilot-spezialisierung.html
  - Responsible AI — 7 principles incl. accountability and lifecycle governance, EU AI Act aligned: https://www.tietoevry.com/en/campaigns/responsible-ai
  - 2026 outlook: "innovation only succeeds when people trust it"; responsible AI "essential for AI adoption in highly regulated environments": https://www.tieto.com/en/insights/2026/expert-insights-technology-2026
  - Indtech job ad: "AI-first and agentic-first" vision for public-sector software (Public 360°).
  - **No public Tieto stance on AI code review found** — the gap our concept fills.
- **Regulated domains:** banking (DORA), healthcare (Lifecare, 10M+ Nordic citizens), public sector (case management, automated decisions only "where legally permitted"), telecom R&D.
- **Previous Junction:** 2023 "PainMgmt: Safer Solutions" (safety + real-world impact).

**Implication for the pitch:** speak the language of audit trails, named accountability, release gates and regulated customers. Position the concept as the missing, defined "review merge requests" step inside Tieto's existing agentic pipeline.

---

## 2. The bottleneck — data

| Stat | Source |
| --- | --- |
| Agent tokens overtook human tokens ~6 Feb 2026; ~7.3T/day (7-day avg) by Aug 2026, ~5x human. **Fact-check: primary post supports only "nearly 5x as many tokens as humans" and "~14X since February"; 7.3T and Feb 6 crossover are from chart/secondary coverage.** Note: daily rate, not monthly total; >85% cached prompts. | a16z/OpenRouter via https://www.eweek.com/news/ai-agents-llm-token-usage-humans/ |
| Google: ~75% of new code AI-generated and engineer-approved (Apr 2026) | https://www.semafor.com/article/04/24/2026/google-ceo-says-75-of-companys-new-code-is-ai-generated |
| High-AI teams merge +98% PRs, review time +91% [vendor] | https://www.faros.ai/blog/ai-productivity-paradox-report-2025 |
| AI PRs wait 4.6x longer for pickup; accepted 32.7% vs 84.4% manual [vendor] | https://linearb.io/resources/engineering-benchmarks-report |
| Experienced devs 19% slower with AI, felt 20% faster (RCT) | https://arxiv.org/abs/2507.09089 |
| +25% AI adoption ≈ −7.2% delivery stability (DORA 2024); instability still rising (DORA 2025) | https://cloud.google.com/blog/products/devops-sre/announcing-the-2024-dora-report |
| AI-assisted PRs 1.7x more issues, 1.57x more security issues [vendor] | https://www.coderabbit.ai/blog/state-of-AI-vs-human-code-generation-report |
| Median PR size 68 → 122 lines Jun 2025–Jun 2026 [vendor] | https://www.greptile.com/state-of-ai-coding |
| Duplicated code blocks 8x in 2024 [vendor] | https://leaddev.com/software-quality/how-ai-generated-code-accelerates-technical-debt |
| Faros 2026: median review time +441% | [UNVERIFIED] |

**One-line framing:** generation scaled ~exponentially; review is still human-paced, so either review becomes the bottleneck or it becomes rubber-stamping. Both are failures.

---

## 3. What industry does (prior art to reference and differ from)

- **Meta RADAR** (arXiv 2605.30208, May 2026) — closest to the challenge: eligibility → static heuristics → Diff Risk Score → LLM review → deterministic validation; low-risk diffs auto-approved, rest to humans. Reported revert rate ~1/3 and incidents ~1/50 vs baseline, −35% review time. [read from summaries — verify against paper] https://arxiv.org/html/2605.30208
- **Meta Diff Risk Score:** LLM predicts SEV probability per diff; let 10k+ changes land during a freeze. https://engineering.fb.com/2025/08/06/diff-risk-score-drs-ai-risk-aware-software-development-meta/ — open analogue DRS-OSS: https://arxiv.org/abs/2511.21964
- **Anthropic Claude Code Review** (Mar 2026): parallel agents → verification step → severity ranking; <1% findings marked incorrect [vendor]; ~$15–25/review. https://claude.com/blog/code-review
- **GitHub Copilot code review:** 60M+ reviews; agentic, full-repo context; reviews bot-authored PRs since Aug 2026. https://github.blog/ai-and-ml/github-copilot/60-million-copilot-code-reviews-and-counting/
- **Google Critique:** ML-suggested edits resolve ~7.5–8% of reviewer comments. https://research.google/blog/resolving-code-review-comments-with-ml/

**Common principles:** route by risk · full repo context · verify findings before posting · low noise, severity-ranked · measure outcomes (reverts, incidents, acceptance), not activity.

**Where we can differ (Tieto's brief emphasis):** existing systems output a *score* or *comments*. The brief wants *evidence traceable to a requirement*, explicit *abstentions*, and a *signed human decision record* (checked / not checked / residual risk). Meta auto-approves; Tieto insists AI is advice, never approval.

---

## 4. Failure modes to name

- **Prompt injection via PR content** — CamoLeak (CVSS 9.6), hidden markdown in PR text exfiltrated private code via Copilot Chat. https://legitsecurity.com/blog/camoleak-critical-github-copilot-vulnerability-leaks-private-source-code
- **Self-preference / correlated errors** — LLM judges favour own outputs: https://arxiv.org/abs/2404.13076 ; persists with rubrics: https://arxiv.org/abs/2604.06996. Mixing models helps partly [UNVERIFIED preprint 2610.01471].
- **Noise / alert fatigue** — low acceptance of AI output (LinearB 32.7%).
- **False reassurance** — METR perception gap; tests written by the same agent that wrote the code (no hard data; mitigation = mutation testing).
- **Hallucinated packages** — 19.7% of package refs in LLM code non-existent (USENIX Sec 2025) [secondary].
- **Stale evidence** after a new commit; persuasive but wrong explanations.

---

## 5. Building blocks for the concept

- **Deterministic first:** Roslyn analyzers / compiler diagnostics for C#: https://learn.microsoft.com/en-us/dotnet/fundamentals/code-analysis/overview
- **Test the tests:** mutation testing — Meta ACH (73% of generated tests accepted): https://arxiv.org/abs/2501.12862 ; C#: Stryker.NET https://stryker-mutator.io/docs/stryker-net/introduction/
- **Abstention / selective prediction for code:** https://arxiv.org/pdf/2605.19369 , https://arxiv.org/pdf/2605.17029 , https://arxiv.org/pdf/2604.06723
- **Provenance:** SLSA/in-toto/Sigstore prove *how built*, not *who/what wrote it*. Proposals: AI-BOM via in-toto (https://todogroup.org/blog/2026-07-14-verifiable-provenance-ai-assisted-contributions/), AIIR receipts (https://pypi.org/project/aiir/). → The human decision record could be an in-toto-style signed attestation bound to the revision.

---

## 6. Regulation (why accountability matters to Tieto's customers)

- **Cyber Resilience Act:** exploited-vuln reporting (24h) applies from 11 Sep 2026; most obligations Dec 2027. Manufacturer liable regardless of who/what wrote the code (our inference). https://www.jonesday.com/de/insights/2026/07/eu-cyber-resilience-act-24hour-reporting-duties-start-september-11-2026
- **NIS2 Art. 21(2)(e):** security in development and maintenance; management accountable.
- **DORA (finance, applies since Jan 2025):** ICT change management and testing → Banktech customers.
- **EU AI Act:** coding assistants generally not high-risk; Art. 14 "human oversight" is useful vocabulary; Art. 4 AI literacy applies. High-risk deadlines likely delayed (Digital Omnibus, not confirmed adopted).
- No regulator guidance specific to AI-generated code found.

---

## 7. Sample repo — branch assessment

Repo: https://github.com/te-industry-tech-office/junction26-messagepack-csharp (read-only copy at `/tmp/junction-research/repo`; nothing built or run). All four branches: one agent commit on base `32258fdb`. All upstream issues still open.

| Branch | Requirement | Change | Demo fit |
| --- | --- | --- | --- |
| **ju26-issue-2283** | Generator/analyzer crash (`IndexOutOfRangeException`) on closed generic value type from referenced assembly → no resolver → runtime failure under AOT | ~29 lines `TypeCollector.cs` + 189 lines tests + docs | **Recommended** — small, precise requirement with repro, real finding, upstream PR #2305 to compare |
| ju26-issue-2297 | `[ExcludeFromCodeCoverage]` on generated code | small template edits; 237 files mostly regenerated snapshots | Backup — possibly unneeded `#if !NETSTANDARD2_0 && !NETFRAMEWORK` guard; possible CS0579 duplicate attribute on user partials [inferred] |
| ju26-issue-2234 | One-line issue: analyzer broken with `SuppressSourceGeneration = true` | ~22 lines + tests | Weak — agent inferred root cause; good only as "unclear requirement" abstention |
| ju26-issue-2129 | Feature: generate formatter for type from another assembly | ~1,034 lines / 28 files, new public API, 4 analyzer IDs | Too big; public API never agreed with maintainer |

### Worked example candidate: ju26-issue-2283 (commit `9df83c38`)

Change: `DeclaringSyntaxReferences[0]` → `FirstOrDefault()` (`TypeCollector.cs:1077`) and new `GetPropertyIdentifierLocation` helper (`:985`, `:1434`); **plus** a new `ReportIfLocatedInCompilation` filter (`:239`, `:1444-1450`) that drops *every* diagnostic whose location is not in the current compilation's source.

**Candidate findings** (to be verified by executing a test before presenting):
1. **Positional record diagnostics silently vanish** [inferred] — helper only matches `PropertyDeclarationSyntax`; for `record R([property: Key((string)null)] int X)` it returns null → `Location.None` → dropped by filter. Previously crashed; now silent. MsgPack005 lost for source types. Upstream #2305 handles `ParameterSyntax`. *Verify:* analyzer test expecting MsgPack005 on a positional record.
2. **Filter broader than the bug, with incorrect justification** [read + inferred] — wraps all diagnostics (e.g. PartialTypeRequired at `:1393`); remark claims analyzers can't report such locations, but `Location.None` is permitted (Roslyn rejects only source locations from foreign syntax trees — confirm in Roslyn docs). Untested behaviour change.
3. **Test enshrines suppression** [read] — `GenericsFormatterTests.cs:590` asserts zero diagnostics for an unkeyed member in a referenced type; claim "the defining project reports it" is never exercised (defining assembly compiled without analyzer).

**Candidate abstentions:**
1. **Drop vs report at `Location.None`?** Agent drops, upstream #2305 reports. Maintainer policy decision; #2305 unmerged, no maintainer comment → AI must not decide; route to named owner.
2. **Generated output for unkeyed metadata member unchecked** — tests set `SkipGeneratedSourcesCheck` (~line 641) and only assert resolver exists; correctness of serialization round-trip needs build + runtime execution.

**Natural outcome for the demo:** "request changes" — not a forced approval.

---

## 8. Items to verify before presenting

- RADAR numbers (read the paper), Faros +441%, cross-model preprint, a16z original chart.
- Roslyn rule on `Location.None` vs foreign syntax tree locations.
- Finding 1 for 2283 — run an actual analyzer test on the branch (sandboxed).
- `ExcludeFromCodeCoverageAttribute` availability on netstandard2.0 (only if using 2297).

---

# Part 2 — How top companies do it, and existing solutions

## 9. Big tech practices (beyond RADAR / Copilot / Critique)

| Company | Mechanism | Numbers | Source |
| --- | --- | --- | --- |
| **Cloudflare** (closest real-world analogue) | Risk tiers by diff size: trivial (≤10 lines, 2 agents, cheaper model) / lite (≤100 lines, 4 agents) / full (7+ specialists: security, perf, quality, docs, release, standards, AGENTS.md). `auth/`, `crypto/` always full. Bot can approve, revoke or block; humans override with **"break glass"** | 131k runs / 48k MRs / 5k repos in 30 days; median $0.98, P99 $4.45 per review; break glass 0.6% | https://blog.cloudflare.com/ai-code-review/ |
| **Uber uReview** | Generate → filter → separate grader model → dedupe; re-run 5× on final commit to judge "addressed" (LLM nondeterminism) | >90% of ~65k diffs/week; 75% comments useful, 65% addressed | https://www.uber.com/blog/ureview/ |
| **Microsoft** | AI reviewer on every PR as a participant; changes attributed in commit history "preserving accountability" | 600k+ PRs/month; 10–20% faster median completion [vendor] | https://devblogs.microsoft.com/engineering-at-microsoft/enhancing-code-quality-at-scale-with-ai-powered-code-reviews/ |
| **Stripe Minions** | "Blueprints": deterministic steps (lint, push) + agent steps; max 2 CI rounds then back to human; two humans (operator + reviewer) | 1,300+ PRs/week "human-reviewed, but containing no human-written code" | https://stripe.dev/blog/minions-stripes-one-shot-end-to-end-coding-agents-part-2 |
| **OpenAI** | Codex reviews every internal PR; **precision over recall**; nits "can have negative value" | 52.7% of comments → code change | https://alignment.openai.com/scaling-code-verification/ |
| **Atlassian RovoDev** | AI reviewer, 1-year study (observational) | −30.8% PR cycle time, 1,900+ repos | https://arxiv.org/abs/2601.01129 |
| **Amazon** | Mar 2026: senior sign-off on AI-assisted changes (Retail) after outages — scope disputed by Amazon. **Kiro specs:** requirements.md (EARS) → design.md → tasks.md traced to requirements; SMT-based requirements gap analysis [UNVERIFIED] | — | https://the-decoder.com/amazon-makes-senior-engineers-the-human-filter-for-ai-generated-code-after-a-series-of-outages/ , https://kiro.dev/docs/specs/concepts |
| **Spotify** | Honk agents + Fleet Management auto-merge after checks. Oct 2026: dependency bump passed all checks, broke prod — "change volume outpaced verification controls"; fix: rollback capacity, run during owner team hours | 1,500+ AI PRs; 2.5M+ fleet PRs | https://infoq.com/news/2026/10/spotify-ai-quality-controls |
| **Google** | AutoCommenter: every comment links to a best-practice doc, confidence-thresholded, staged rollout. OCTO team: AI risk summary per PR, mandatory AI tests, **"Conditional LGTM"** (approval valid only if tests pass), no nits on agent code, "quiet hours" vs approval fatigue | 68% of top cited best practices covered | https://arxiv.org/abs/2405.13565 , https://cloud.google.com/transform/when-ai-writes-the-code-who-reviews-it-cto-google-cloud |
| **Meta ACH / TestGen-LLM** | Mutation-guided tests; tests must build, pass reliably, increase coverage before human sees them | 73% accepted | https://arxiv.org/abs/2501.12862 |
| **Airbnb** | Step-wise migration with validation gates and retry loop | 3.5k files in 6 weeks, ~97% automated | https://airbnb.tech/?p=366 |
| **Coinbase** | Security-critical financial code excluded from AI generation | 40% AI-written (Sep 2025) | https://www.theblock.co/post/369460/brian-armstrong-coinbase-ai |

Podcasts: Pragmatic Engineer w/ Charity Majors ("code review is overrated", Aug 2026); Dev Interrupted (accountability-oriented review, Jul 2026).

**Patterns:** AI reviewer on every PR, humans own merge · risk tiers with forced escalation for sensitive paths · precision over recall (grader/filter) · deterministic gates wrap the agent with capped retries · named human ownership · measure usefulness · failures come from volume outrunning verification.

## 10. Quant firms and high-assurance organisations

- **Jane Street — Iron code review:** ownership is version-controlled metadata per path; per-file **"scrutiny" level** sets required reviewers (n of k); explicit feature-review sign-off; reviewers see only what changed since their last approval; "If you haven't fully reviewed a branch, you can't release it." https://www.janestreet.com/tech-talks/janestreet-code-review
  - AI tooling: CES applies model diffs to pre-warmed builds → green/red signal. First AI review model learned to reply "I'll do the review tomorrow" — imitation ≠ the task. https://ai.engineer/talks/building-ai-powered-developer-tools-at-jane-street (summary)
  - Yaron Minsky (Jun 2026): "Agentic code ... still tends towards slop." "The verification bottleneck is more important than ever." "Tests aren't enough!" → investing in formal methods. https://blog.janestreet.com/formal-methods-at-jane-street-index
  - Agents may delete failing tests to make them pass [UNVERIFIED summary].
- **Optiver** ("Engineering the Agentic SDLC", Jun 2026): agents "claim success when they haven't" → **removed self-certification**; completion judged by captured-traffic tests and E2E pass/fail; phase gates; humans keep "architectural review, risk calls, and novel domains". https://www.optiver.com/insights/technology-blog/engineering-the-agentic-sdlc/
- **Two Sigma:** "each of us must remain a watchful supervisor"; agents may get better at "justifying or hiding their reasoning". https://www.twosigma.com/articles/ai-in-investment-management-2026-outlook-part-i
- Citadel, HRT, D. E. Shaw: job ads / snippets only. Jump, IMC, SIG, RenTech: nothing public.
- **Banks:** Goldman pilots Devin agents "supervised by humans"; JPMorgan 10–20% productivity (unclear measurement); Morgan Stanley DevGen.AI produces specs humans rewrite (~280k hours saved). No public review policy.
- **Safety-critical (DO-178C / ISO 26262):** no qualified AI codegen tool found; pattern = keep LLM out of the qualified path, verify outputs with qualified deterministic tools, trace artifacts to prompt + model version [UNVERIFIED].
- **Verified generation:** vericoding benchmark — LLMs succeed 82% Dafny / 44% Verus / 27% Lean. https://arxiv.org/abs/2509.22908 ; Kleppmann: have AI produce proofs instead of reviewing output. https://martin.kleppmann.com/2025/12/08/ai-formal-verification.html

**Transferable lessons:** ownership as metadata · per-path scrutiny tiers · no agent self-certification · flag deleted/weakened tests · review only deltas since last approval · evaluate the reviewer on outcomes, not human-likeness.

## 11. Existing products vs Tieto's requirements

R1 risk routing · R2 requirement traceability · R3 explicit abstention · R4 tool-verified vs LLM-inferred · R5 signed human decision record · R6 track misses, per-area trust · R7 outcome metrics · R8 prompt-injection resistance

| Product | R1 | R2 | R3 | R4 | R5 | R6 | R7 | R8 | Note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CodeRabbit (Agentic Change Mgmt) | Y | N | N | P | N | P | P | N | Triage routes to humans; $1.5B valuation [vendor] |
| Qodo 3.0 | P | **Y** | N | N | N | P | P | N | Ticket compliance vs Jira/Linear criteria |
| Baz Spec Reviewer | N | **Y** | N | P | N | N | N | N | Checks PR vs Jira + Figma |
| Aviator Verify | P | **Y** | P | **Y** | P | N | N | N | Deterministic vs "AI fallback" labels |
| Cursor Bugbot (+Graphite) | N | N | N | N | N | P | P | N | Learned rules from reactions |
| Greptile | P | N | N | N | N | P | N | N | Opaque 0–5 confidence score |
| GitHub Copilot review | N | N | N | P | N | N | N | **N** | Hit by "Comment and Control" injection |
| Claude Code Review / Action | N | N | N | N | N | N | N | **N** | CVSS 9.4 PR-title injection |
| OpenAI Codex review | P | N | P | N | N | N | N | N | Only P0/P1 posted |
| LinearB gitStream | **Y** | P | N | P | N | N | **Y** | N | Rule-based auto-approve low risk |
| Semgrep Assistant | N | N | P | **Y** | N | P | P | N | Rule hit vs AI triage separated |
| Sonar AI Code Assurance | P | N | N | Y | N | N | P | N | Manual AI-code tagging, stricter gate |
| Mergify | P | N | N | N | N | N | Y | N | Merge-queue break-main data |
| Cursor Agent Trace / git-ai | P | N | N | N | N | N | N | N | Per-line AI authorship (provenance) |

Sources: coderabbit.ai/blog/introducing-agentic-change-management · qodo.ai/blog/introducing-qodo-3.0 · baz.co/spec-reviewer · aviator.co/verify · cursor.com/blog/bugbot-learning · linearb.io · semgrep.dev/blog/2025/announcing-ai-noise-filtering-and-triage-memories · github.com/cursor/agent-trace · labs.cloudsecurityalliance.org (Comment and Control). Most numbers [vendor].

**Benchmarks:**
- Martian Code Review Bench (17 tools, open): top F1 ≈ 51% in Jan–Feb 2026 runs, later 60–65% (Qodo 64.3%, Cubic 64.9%) — **all from secondary sources, verify on codereview.withmartian.com**; Bugbot 68% precision / 36.7% recall (secondary only); offline and online rankings disagree. https://codereview.withmartian.com
- Tenki: top recall 68.9% at 0.30 precision. https://tenki.cloud/blog/benchmarking-ai-code-reviewers
- Vendor benchmarks are each won by their sponsor.
- **No benchmark measures calibration, abstention, or downstream misses.**

## 12. Answer: is this already solved?

**No.** Each piece exists somewhere: routing (CodeRabbit, gitStream, Cloudflare), requirement traceability (Qodo, Baz, Aviator, Kiro), deterministic-vs-AI separation (Semgrep, Aviator), per-path ownership and scrutiny (Jane Street Iron). **Nobody** combines them, and nobody provides:
- **R3 explicit abstention record** ("I did not decide X because Y; human action needed: Z")
- **R5 signed human decision record** (checked / not checked / residual risk / owner, bound to revision)
- **R6 miss tracking** — tools learn from comments they made, never from bugs they missed (reverts/incidents traced back), and never withdraw trust per area
- **R8** — major reviewers had critical injection CVEs in 2026

**Positioning:** not another reviewer competing on bug-finding F1 (~50–65% at best), but an **accountability layer** that consumes existing reviewers and analyzers, routes by per-path risk (Iron + Cloudflare), forbids self-certification (Optiver), records abstentions, and produces a signed decision record whose outcome feeds back into per-area trust. Watch: CodeRabbit's "control layer" (Aug 2026) and Qodo 3.0 governance are moving toward this — differentiate explicitly.

**Slide quotes:**
1. "If you haven't fully reviewed a branch, you can't release it." — Jane Street
2. "The verification bottleneck is more important than ever ... tests aren't enough!" — Yaron Minsky, 2026
3. Agents "claim success when they haven't" — Optiver, 2026
4. Cloudflare: 48k MRs/30 days, median $0.98/review, human "break glass" 0.6%
5. Stripe: 1,300+ PRs/week "human-reviewed, but containing no human-written code"
6. Best AI reviewers ≈ 50–65% F1 (Martian, secondary) → AI can advise, not gate

**Verify before slides:** Jane Street wording (from summaries, check videos), Cloudflare InfoQ follow-up numbers, Kiro SMT 60% figure, Amazon policy scope.

---

# Part 3 — Formal verification, model checking and program analysis

## 13. Industry practice

**Google Tricorder / Error Prone** (Sadowski et al., CACM 2018 — quotes verified from full text, https://6826.csail.mit.edu/2020/papers/google-analysis-cacm.pdf):
- "Developers, not tool authors, will determine and act on a tool's perceived false-positive rate."
- Code-review checks must "Produce less than 10% effective false positives." Analyzers over 10% "Not useful" get disabled until fixed.
- "Do not just find bugs, fix them." / "Code review is a sweet spot for displaying analysis warnings."
- Central dashboards failed: "few of them actually made such a visit."

**Meta Infer / Zoncolan** (Distefano, Fähndrich, Logozzo, O'Hearn, CACM 2019, https://discovery.ucl.ac.uk/10084236/1/O%27Hearn%20AAM%20scaling-static-analysis-at-facebook.pdf):
- Batch mode: "the fix rate… was near zero." At diff time: "rocketed to over 70%. The same program analysis, with same false positive rate, had much greater impact when deployed at diff time."
- Diff-time analysis ~15 min avg; "if a bot were to run for an hour or more on a diff it could be too late." RacerD ~50% fix rate. Zoncolan finds 43.3% of severe security bugs.

**AWS:** Zelkova ~a billion SMT queries/day (https://amazon.science/blog/a-billion-smt-queries-a-day); Cedar "verification-guided development" — Lean/Dafny model + proofs, Rust prod checked by differential random testing against the model (https://arxiv.org/abs/2407.01688); Bedrock Automated Reasoning checks GA Aug 2025 ("up to 99%" [vendor]); Kiro Requirements Analysis — LLM → logic → SMT finds contradictions/gaps (https://kiro.dev/blog/deep-spec-analysis/). TLA+ / P / Kani / SAW not re-verified this pass.

**Microsoft:** Z3, SLAM/SDV, CodeQL, F*/Project Everest, Dafny, Roslyn; Infer# for .NET (low maintenance since ~2023 [UNVERIFIED]).

**Others:** Datadog TLA+ → runtime monitors (https://www.datadoghq.com/blog/engineering/continuous-formal-spec-validation); MongoDB TLA+ conformance checking (https://mongodb.com/blog/post/engineering/conformance-checking-at-mongodb-testing-our-code-matches-our-tla-specs).

## 14. Finance

- **Imandra** — clearest public case: SIGMA X MTF auction verification (https://ocaml.org/success-stories/financial-compliance-with-automated-reasoning); UBS ATS SEC-fine case study (https://www.imandra.ai/case-study-2015-sec-fine-against-ubs-ats/); **CodeLogician** — LLM builds formal models, ImandraX reasons; claims closing a 41–47 point accuracy gap vs LLM alone (https://arxiv.org/abs/2601.11840).
- Jane Street — OCaml types as everyday verification; 2026 formal-methods push (see §10).
- Citadel, HRT, Two Sigma, Jump, Bloomberg: no public formal-verification record. DeFi (Certora, Runtime Verification) is the most active finance-adjacent field.

## 15. Verifying AI-generated code

- Vericoding (https://arxiv.org/abs/2509.22908): Dafny 82% / Verus 44% / Lean 27%.
- AlphaVerus (https://arxiv.org/abs/2412.06176): verifier-feedback loop with explicit filter against **spec-trivializing reward hacking**.
- IRIS (https://arxiv.org/abs/2405.17238): LLM infers taint specs, CodeQL checks — 55/120 vulns vs 27 for CodeQL alone, but ~85% false discovery rate.
- Kleppmann (https://martin.kleppmann.com/2025/12/08/ai-formal-verification.html): AI makes proofs cheap; the spec stays hard.
- Startups: Axiom ($200M, Lean, https://siliconangle.com/2026/03/12/verifiable-ai-startup-axiom-raises-200m-prove-ai-generated-code-safe/), Theorem (YC S25, https://venturebeat.com/security/theorem-wants-to-stop-ai-written-bugs-before-they-ship-and-just-raised-usd6m), Harmonic, Galois.

## 16. Practical for C# / MessagePack

- Roslyn `ControlFlowGraph.Create` (https://learn.microsoft.com/en-us/dotnet/api/microsoft.codeanalysis.flowanalysis.controlflowgraph), `SemanticModel.AnalyzeDataFlow`, `AnalyzeControlFlow` exist; custom fixpoint analyses must be hand-written.
- MessagePack generator tests use `Microsoft.CodeAnalysis.CSharp.SourceGenerators.Testing.XUnit` with ~92 golden expected-output folders under `tests/MessagePack.SourceGenerator.Tests/Resources/` (not Verify library); separate `ExecutionTests` / `MapModeExecutionTests`.
- **Cheapest real evidence for a generator PR:** (1) golden-output diff across all resources, (2) analyzers with warnings-as-errors incl. RS1035, (3) `trackIncrementalGeneratorSteps` caching check, (4) FsCheck round-trip properties, (5) Stryker.NET on generator project, (6) Roslyn CFG/dataflow facts on changed methods.

## 17. Technique table

| Technique | Proves | Cost | PR-review fit | Example |
| --- | --- | --- | --- | --- |
| Compiler / type checks | Well-typed, no banned APIs | ~0 | Gate | Error Prone |
| Analyzers | Absence of specific patterns | Low | Yes, if <10% effective FP | Tricorder, Roslyn |
| Interprocedural static analysis | No null-deref/leak/taint/race on analysed paths | Medium | Diff-time | Infer, CodeQL |
| Golden / snapshot diff | Exact change in generated artifact | Low | Yes | MessagePack Resources/ |
| Unit / execution tests | Behaviour on chosen inputs | Low–Med | Yes | everywhere |
| Mutation testing | Tests can actually fail | Medium | Changed files | Stryker.NET, Meta ACH |
| Property / differential tests | Invariant on many inputs; impl ≈ model | Medium | Yes | AWS Cedar |
| Model checking | Design invariants, all interleavings (bounded) | High (spec) | Design review | AWS, Datadog, MongoDB |
| SMT / policy reasoning | Exhaustive in decidable domain | Medium | Configs | Zelkova |
| Deductive proof | Functional correctness vs spec | Very high | Rarely | seL4, Everest, Cedar |

**Limits:** Rice's theorem (unsound or incomplete); false positives kill trust; seL4 ≈ 25 person-years / ~8,700 lines C (https://trustworthy.systems/projects/OLD/l4.verified/numbers); verified-against-the-wrong-spec.

---

# Part 4 — Jane Street deep dive

Full analysis: [jane-street/analysis.md](jane-street/analysis.md). Primary-text transcripts in [jane-street/transcripts/](jane-street/transcripts/) (podcast transcripts from signalsandthreads.com, official Iron talk transcript, ai.engineer transcript, blog posts). Bug Bash 2026 keynote: abstract only — do not quote. Note: Ron Minsky = Yaron Minsky.

Quotes checked against the raw transcripts:
- "If you haven't fully reviewed a branch, you can't release it." — Ian Henry, Iron talk
- "It deliberately stops and forces you to do the right thing." — same
- "The verification bottleneck is more important than ever." — Y. Minsky, blog 2026-06-07
- "I think in some ways it's harder to verify code that no person wrote." — Ron Minsky, ep. 31
- "…AI agents has kind of broken the social contract around code review… now all you need is a prompt and a dream…" — Ron Minsky, ep. 31, 01:43:33
- "I can have 10 Claude codes all writing code, and it doesn't matter. I'm not going to go any faster if I can't merge those PRs after reviewing them and actually deciding they work." — Will Wilson, ep. 26, ~00:57
- "Mm, I'll do it tomorrow." — Jane Street's trained AI reviewer, quoted by John Crepezzi, AI Engineer Summit 2025, 12:06

> **STATUS: RESEARCH FINDINGS — NOT FINAL.** Research wave A agent output, 2026-11-14. Items marked [secondary]/[UNVERIFIED] must be checked before use on slides; see fact-check-waveB.md.

# RESEARCH FINDINGS — not final
Wave A: trading and market-infra verification, review and AI-code governance (researched 2026-11-14)

Already covered (one line): Jane Street (Iron, expect tests, formal-methods turn), Optiver's "Engineering the Agentic SDLC", Imandra, and Two Sigma's watchful-supervisor outlook.

## 1. Regulation (the strongest material)

**MiFID II RTS 6 (Delegated Reg. 2017/589)** [primary: Commission text, https://ec.europa.eu/finance/securities/docs/isd/mifid/rts/160719-rts-6_en.pdf; consolidated version at EUR-Lex CELEX 32017R0589]
- **Art. 5(2):** "A person designated by the senior management … shall authorise the deployment or substantial update" of an algorithm. A named human signs.
- **Art. 5(4):** the test methodology must show that the algo "(a) does not behave in an unintended manner" and, under stress, "allows for the switching off" of the algo.
- **Art. 5(7):** the record of every material change must show when it was made, "the person that has made the change", "the person that has approved the change" and "the nature of the change". This is an author/approver audit trail.
- **Art. 7:** testing happens in an environment "separated from its production environment".
- **Art. 8:** before deployment the firm sets predefined limits on instruments, order price/value/count, positions and venues. In effect, a small blast radius on first deploy.
- **Art. 9:** annual self-assessment. Risk management writes the report, internal audit audits it, and senior management approves it.
- **Art. 10:** stress tests at **2x** the peak message and trade volume of the last six months.
- **Art. 11(1):** a material change must be reviewed by a designated person, and **"The depth of the review shall be proportionate to the magnitude of the proposed change."** This is regulatory text for tiered LIGHT/STANDARD/DEEP review.
- **Art. 12:** kill functionality. The firm must be able to cancel any or all orders immediately and to identify which algo and trader sent each order.

**ESMA Supervisory Briefing on Algorithmic Trading (26 Feb 2026)** [secondary: law-firm summaries; primary at esma.europa.eu, ref ESMA74-1505669079-10311]
- A material change is "any modification that may alter the behaviour, risk profile, or compliance posture."
- Firms must assess the **cumulative effect of incremental changes**: several small changes can add up to a substantial update.
- Firms must "recognise any AI that is used in algorithmic trading" and cover it in the annual self-assessment. Hard-block limits should be "hard coded within an algorithm" where possible.
- The briefing does not address AI-written code itself. That is a gap Decision-First Review can fill.
- Sources: https://www.macfarlanes.com/insights/102mpep/algorithmic-trading-and-artificial-intelligence-esma-supervisory-briefing/ and https://cms.law/en/deu/legal-updates/esma-supervisory-briefing-on-algorithmic-trading-in-the-eu-key-points-and-practical-implications

**UK FCA multi-firm review of algo controls (21 Aug 2025, 10 principal trading firms)** [primary] https://www.fca.org.uk/publications/multi-firm-reviews/algorithmic-trading-controls-high-level-observations
- Good practice:
  - some firms had *all* algo changes, "whatever their materiality", approved by a Senior Management Function;
  - small pilot trades in production;
  - an algo inventory listing owner, approved operators and risk parameters.
- Room for improvement (FCA wording — fact-check: not labeled "poor practice"):
  - "material change" not defined;
  - simulation that "lacked sophistication";
  - unclear ownership of deployment steps;
  - inventories that did not name the people approved to operate each algo.

**SEC Rule 15c3-5 (Market Access Rule)** [primary] https://www.law.cornell.edu/cfr/text/17/240.15c3-5
- Pre-trade controls must reject orders exceeding "appropriate price or size parameters" and catch "duplicative orders".
- Controls must stay under the firm's "direct and exclusive control".
- The firm must review its controls at least annually, and **the CEO must certify every year** that the controls comply.

**Knight Capital, SEC Order 34-70694 (16 Oct 2013)** [primary] https://www.sec.gov/files/litigation/admin/2013/34-70694.pdf
- What went wrong in the code:
  - Power Peg had been dead since 2003 but was "present and callable".
  - The new RLP code "repurposed a flag that was formerly used to activate the Power Peg code".
  - In 2005 a function Power Peg depended on was moved, and Power Peg was never retested.
- What went wrong in the deploy:
  - A technician did not copy the new code to one of eight servers.
  - "Knight did not have a second technician review this deployment", and it had "no written procedures that required such a review."
- Alerts were ignored: 97 automatic "Power Peg disabled" emails went out from 08:01, before the open, and nobody acted on them.
- Rollback made it worse: Knight "uninstalled the new RLP code from the seven servers where it had been deployed correctly". The old flag then hit dead code on all eight servers.
- Result: 4M executions in 154 stocks in ~45 minutes, and a **$460M** loss (the SEC figure; the often-quoted $440M is Knight's earlier estimate). Fined $12M under 15c3-5.

**Citigroup, FCA/PRA (May 2024)** [primary] https://www.fca.org.uk/news/press-releases/fca-fines-cgml-27-million
- A trader keyed in a $444bn basket instead of $58M.
- Controls blocked $255bn, but $189bn reached an algo, and $1.4bn was sold in Europe.
- Fines of £61.6M in total. A recent case showing that pre-trade control code is itself critical.

## 2. Firms

**Optiver, beyond the agentic blog post**
- **Carl Cook, CppCon 2017 "When a Microsecond Is an Eternity"** [primary, slides]: the rig has a server that replays exchange market data, the server under test, and a capture/parse server, with switch timestamping.
  - The talk argues microbenchmarks are "not representative" and only a production-like replay setup can be trusted.
  - The risk check sits inline: `CheckRiskLimits(); SendOrder();`.
  - Slides: https://www.smallake.kr/wp-content/uploads/2023/04/When-a-Microsecond-Is-an-Eternity-Carl-Cook-CppCon-2017.pdf
- **FPGA post (May 2025)** [primary]: risk is managed "through thorough automated testing, simulations and peer reviews", going from idea to verification to release "in hours or days". https://optiver.com/insights/technology-blog/fpga-hardware-at-optiver-making-impact-at-speed-and-scale/
- **"Building visibility into a CI platform" (May 2026)** [primary]: AI-assisted development is making changes more frequent and is coming from more contributors. Hardware-bound tests (FPGA, kernel-adjacent, latency) need owned bare-metal CI. https://optiver.com/insights/technology-blog/building-visibility-into-a-ci-platform/
- **"Designing for latency and research iteration" (Jul 2026)** [primary]: "Keeping simulation honest relative to production matters." https://www.optiver.com/insights/technology-blog/designing-for-latency-and-iteration/
- I found no Optiver talk specifically on sanitizers or fuzzing [UNVERIFIED that none exists]. David Gross's CppCon 2024 talk is about latency, not testing.

**Hudson River Trading** [primary]
- **"How We Verify Custom Hardware" (2021):**
  - Verilator plus cocotb, with co-simulation driving the design from Python and C++;
  - Jenkins CI that "tr[ies] new pseudo-random seeds", runs tests on lab FPGAs and handles deployment;
  - UVM concepts reused but not UVM itself; formal methods not mentioned.
  - https://www.hudsonrivertrading.com/hrtbeat/verify-custom-hardware/
- **Python type annotations (Feb 2024):** mypy over "millions of lines of Python" from hundreds of developers. Type checking shows which downstream systems a shared-logic change affects, and the post says tests only cover the scenarios someone wrote. https://www.hudsonrivertrading.com/hrtbeat/building-robust-codebases-with-pythons-type-annotations/
- **Python dependency graph (Jun 2023):** teams write rules limiting what their modules may import, and **CI enforces the rules**. A flow network finds which import edges to cut. https://www.hudsonrivertrading.com/hrtbeat/dependency-graph-python-codebase/

**G-Research (London quant firm, new find)** [primary, 13 May 2026] https://www.gresearch.com/news/building-a-code-review-tool-the-llm-patterns-that-actually-work/
- An LLM reviewer runs in CI on every branch.
- Each finding is checked against a rules index built from the standards document: "the model can suggest, but never define." Severity is derived from RFC 2119 levels in code, not by the model.
- Two passes: first for recall, then a separate pass to remove false positives.
- A new model is adopted only if it hits 100% recall on MUST rules and >85% precision.
- It does not block merges, and "There is still a human involved."

**Susquehanna (SIG)** [primary-ish, job ad] https://careers-sig.icims.com/jobs/8819/job
- The Developer Productivity (HPC) team catches "bad code with continuous integration (TeamCity), static analysis, profiling/coverage tools". I found no public SIG blog on review.

**Two Sigma, beyond the outlook** [primary]
- Before releasing preemption in its Cook scheduler, Two Sigma "wrote a simulator … and ran a 7 day production trace".
- The open-source simulator compares two scheduler versions on the same trace and keeps the same simulator version for fair A/B. This is differential replay as a release gate.
- https://www.twosigma.com/articles/cook-a-fair-preemptive-resource-scheduler-for-compute-clusters/ and https://github.com/twosigma/Cook/blob/v1.59.3/scheduler/docs/simulator.md

**Jump (Firedancer), Citadel Securities** [secondary]: Jump ran a $1M public audit contest for Firedancer (2026, 809 reports, many AI-assisted). Citadel Securities says new engineers are hired as managers of agents. Neither has published how it reviews code.

**IMC, DRW, Flow Traders, XTX, Virtu, Tower, Akuna, Da Vinci, Maven:** no concrete public material on verification or review found in this pass [UNVERIFIED]. These firms publish little.

## 3. Exchanges and matching engines
- **Deutsche Börse/Eurex** [primary]: a release simulation environment ahead of each T7 release, plus a self-service T7 Cloud Simulation instance for participants. This is the venue side of RTS 6 Art. 6 conformance testing. https://www.eurex.com/ex-en/support/technology/t7-cloud-simulation
- **Verified matching** [primary, academic]: continuous double auctions formalised in Coq and extracted to OCaml/Haskell. The extracted program was run on real exchange trade logs to check for violations; the exchange is not named in the abstract. Related trade-checker work: arXiv 2210.05447. https://arxiv.org/abs/2410.18751
- I found no public evidence of TLA+ or model checking at Nasdaq, CME or LSEG matching engines (beyond Imandra) [UNVERIFIED].
- **FPGA formal verification:** SymbiYosys and JasperGold appear in industry tooling discussions. No HFT firm publicly confirmed using them in this pass [UNVERIFIED]. HRT's own post describes simulation plus random seeds, not formal methods.

## What Decision-First Review should take from trading
1. **Proportionate review depth as policy, not taste.** RTS 6 Art. 11(1) requires review depth "proportionate to the magnitude of the proposed change". Make LIGHT/STANDARD/DEEP the explicit implementation, with the tier rule written down. That fixes the FCA's "material change not defined" finding.
2. **A named approver separate from the author on every material change.** RTS 6 Art. 5(2)/(7) requires recording who changed it, who approved it, when, and what. The agent is the author and can never be the approver.
3. **Kill-switch, pre-trade-limit and risk-check paths are always DEEP.** These are 15c3-5(c) and RTS 6 Art. 12 controls, and the Citi and Knight losses both went through them.
4. **Dead-code and flag-reuse detector.** Flag any PR that reuses an existing flag, enum value or config key, or that touches code with no recent callers or tests. That is the Knight pattern. Removing dead code should be its own reviewed decision.
5. **Cumulative-drift tripwire.** Per ESMA, many LIGHT PRs to the same module within a window add up and escalate to DEEP.
6. **Replay-based differential behaviour check.** Replay a captured input trace through the old and new builds and diff the outputs (Cook's replay rig, Two Sigma's 7-day scheduler trace). Present the diff as evidence, not as a pass/fail gate.
7. **Deploy and rollback are reviewable artefacts.** Knight lost money on a deploy step and then on a rollback. Require a second-person check of the deploy manifest (all 8 servers?) and a rollback-safety question in DEEP.
8. **LLM findings are validated against a rule index, and severity is derived deterministically.** G-Research's pattern: the model can suggest but never define, and a new model must hit recall/precision thresholds before adoption.
9. **Blast-radius limits on first deploy.** Like RTS 6 Art. 8, DEEP decisions record a staged rollout or limits (canary or pilot trades, as in the FCA's good practice).
10. **Periodic attestation.** A 15c3-5(e) analog: an owner certifies at a fixed interval that the triage rules and controls still hold, so the signers own the policy as well as individual PRs.

## Slide-quotable
- "The depth of the review shall be proportionate to the magnitude of the proposed change." — MiFID II RTS 6, Art. 11(1) (Delegated Reg. (EU) 2017/589)
- "Knight did not have a second technician review this deployment … Knight had no written procedures that required such a review." — SEC Order 34-70694 (2013). Outcome: 4 million executions in ~45 minutes and a $460M loss.
- "The standards document is the sole source of truth; the model can suggest, but never define." — G-Research engineering, May 2026

> **STATUS: RESEARCH FINDINGS — NOT FINAL.** Research wave A agent output, 2026-11-14. Items marked [secondary]/[UNVERIFIED] must be checked before use on slides; see fact-check-waveB.md.

# RESEARCH FINDINGS — not final

**Wave A: How safety-critical industries earn trust in code, and what they say about AI-written code**
Confidence tags: [primary] = standard, regulator, original paper or NASA document; [secondary] = vendor, consultancy or encyclopedia summary; [UNVERIFIED] = from memory or a single weak source.

## 1. DO-178C and its supplements (aviation)

- **Assurance scales with consequence.** DO-178C sets five Design Assurance Levels (DAL A, catastrophic, down to E, no effect). The number of objectives falls as the level drops: A has 71, B 69, C 62 and D 26. A subset of objectives must be met *with independence*: roughly 30–33 at A and 18–21 at B. Sources disagree on the exact counts, so check them against the RTCA text. [secondary: Wikipedia; Rapita]
- **Review is a defined activity, not a vibe.** It covers reviews and analyses of high-level requirements, low-level requirements, architecture, source code and integration. Each has stated objectives: accuracy, consistency, verifiability, conformance to standards, and traceability. [primary: DO-178C §6.3, from the standard's structure; text paywalled]
- **Independence** means the person who verifies an item is not its author. A tool can supply independence if it is qualified. [secondary]
- **Structural coverage escalates with DAL.** Level C requires statement coverage, B adds decision coverage, and A adds MC/DC plus source-to-object-code correlation. Coverage is a check on whether the requirements-based tests were complete. It is not a goal in itself. When code is found with no coverage, the team must resolve it as dead code, deactivated code, or a missing requirement or test. [secondary: Rapita]
- **Trace data** is bidirectional: requirements → design → code → tests, and back. Code that traces to no requirement is a finding. [primary: DO-178C §5.5 / §11.21, structure]
- **Tool qualification (DO-330)** applies only when a tool *eliminates, reduces or automates* a DO-178C process *and its output is not verified*. Three criteria give five levels, TQL-1 to TQL-5:
  - Criterion 1: a development tool whose output becomes part of the software. This is TQL-1 at DAL A.
  - Criterion 2: a verification tool that also reduces other verification activities.
  - Criterion 3: a tool that can only fail to detect an error. This is TQL-5.
  [secondary: consistent across vendor docs]
- **This is how "credit" works.** A qualified tool's result is accepted in place of a human or test activity, as the Plan for Software Aspects of Certification agreed with the authority sets out. An unqualified tool's output must be verified as if a human had written it. [secondary]
- **DO-333 (formal methods)** lets proof replace some reviews, analyses and tests. Airbus used the Caveat prover for *unit proof instead of unit testing* on part of the A380 flight software (about 30,000 lines of C). Unit testing stayed as the fallback for code that could not be proved. [primary: Souyris et al., ERTS 2006/2008; FM 2009]
- **DO-331 and DO-332:**
  - DO-331 (model-based development) moves review up to the model, with model coverage.
  - DO-332 (object-oriented code) adds checks such as type substitutability (Liskov) and analysis of dynamic memory.
  [secondary]

## 2. Tools and what they prove

| Tool | What it establishes | Certification credit |
|---|---|---|
| **Astrée** (AbsInt/ENS) | Sound abstract interpretation: proves there are *no* runtime errors (overflow, division by zero, out-of-bounds access, invalid pointers). It verified A340 primary flight control code in 2003 and has been used on the A380 since late 2004. | Supports the "proves absence" claim. Airbus uses it in production. [primary: Cousot et al.; AbsInt] |
| **CompCert** | A compiler proved correct in Coq, so the compiled code behaves as the source does. | Qualified by MTU under IEC 60880 Cat. A in 2017. AbsInt states that in 2026 the ATR 42/72 MFC_NG became the first claimed DO-178C/DO-333/DO-330 compiler credit. [primary: ERTS 2018 paper; ATR claim is vendor, secondary] |
| **SCADE KCG** (Ansys) | Generates code from a model with a qualified generator. | Qualified at DO-330 TQL-1, ISO 26262 TCL3 and EN 50716 T3. Ansys says it "eliminates" back-to-back testing and code-level traceability, and reduces verification of the generated code. [secondary: vendor] |
| **SPARK/Ada** (AdaCore) | Proves absence of runtime errors and functional contracts, using GNATprove. | NVIDIA moved security firmware from C to SPARK: over 50 developers trained, components shipping in products, and a SPDM attestation library proven memory-safe. [secondary: AdaCore case study] |
| **Polyspace, Frama-C, IKOS** | Polyspace Code Prover and Frama-C (CEA) give sound proof, like Astrée. NASA IKOS is an open-source abstract-interpretation framework. | Can be qualified as verification tools (Criterion 3, TQL-5). [secondary] |
| **LDRA, VectorCAST, Rapita RVS** | Test execution and structural coverage up to MC/DC, plus checks against coding standards. | Qualified verification tools that produce coverage evidence. [secondary] |

## 3. NASA and space

- **Power of 10** (Holzmann, IEEE Computer 2006) sets 10 rules that a machine can check. They include no recursion, fixed loop bounds, no dynamic memory after initialisation, at least two assertions per function, and zero warnings from compilers and analysers, run daily. The rules were written to be *checkable by tools*. [primary, from memory; widely reproduced]
- **SCRUB** (Holzmann, ISSE 6:311–318, 2010) merges human review comments and reports from several static analysers into one queue. The process has three phases: review, then a developer response to every item, then a closeout meeting. JPL used it to review the millions of lines of Mars Science Laboratory flight code. Its successor, CAE-SCRUB, treats each analyser as a review "peer". [primary: NTRS 20100033572; secondary: CACM, GSAW 2018]
- **NASA-STD-8739.8** (Software Assurance and Software Safety) assigns software classes A–F. **Independent Verification and Validation (IV&V)** is done by an organisation that is separate in its technical work, management and budget, the Katherine Johnson IV&V Facility. [primary, from memory, not re-fetched]
- **SpaceX:** Talks show a C++/Linux flight stack that relies on triple redundancy and heavy simulation and hardware-in-the-loop testing, *not* on formal certification. I found no published review process. [UNVERIFIED]

## 4. Automotive, medical and rail

- **ISO 26262** (automotive) grades risk as ASIL A–D. In Part 8, Tool Impact (TI1/2) combined with Tool error Detection (TD1–3) gives a **Tool Confidence Level**, TCL1–3. Higher TCLs need qualification, by validation or proven-in-use evidence. **MISRA C/C++** is the usual coding standard, and **AUTOSAR** standardises the software architecture. [secondary]
- **IEC 62304** (medical device software) has safety classes A, B and C, and the rigour of detailed design and unit verification grows with the class. FDA's 2023 premarket software guidance sets "Basic" or "Enhanced" documentation by risk. [secondary]
- **EN 50128 → EN 50716:2023** (rail) uses SIL 0–4 and tool classes T1, T2 and T3. Formal methods are "highly recommended" at SIL 3–4. Paris Metro Line 14 (Météor) used the B-method with Atelier B: about 86,000 lines of generated Ada, with roughly 27,000 proof obligations discharged. ClearSy reports *no bugs found after proof* and none in operation since 1998. The claim that Line 14 needed no unit tests could not be verified. [secondary: ClearSy/arXiv 2005.07190]

## 5. AI-generated code in safety-critical settings

- **EASA's AI Concept Paper (Issue 02)** sets AI levels:
  - 1A: human augmentation.
  - 1B: cognitive assistance to the human.
  - 2A: human–AI cooperation.
  - 2B: human–AI collaboration.
  - 3A: the AI makes decisions and acts, and a human can override it.
  - 3B: the AI makes decisions and acts, and no human can override it.

  Its key idea is "learning assurance". **The paper covers AI in aviation systems and operations (Levels 1–2 only; Level 3 deferred), not AI used as a software development tool** (fact-check corrected). I found no section on LLM code generation. [primary: EASA PDF]
- **FAA AI Safety Assurance Roadmap v1 (2024)** separates static "learned" AI from "learning" AI. It is also about AI in the product, and it is deliberately non-prescriptive. [primary: faa.gov/media/82891]
- **SAE G-34 / EUROCAE WG-114** are developing ARP6983 / ED-324 for certifying ML in aircraft systems. Same scope: AI in the product. [UNVERIFIED on status]
- **The gap is the opening for the concept.** Under DO-178C, an LLM is an *unqualified development tool*. It cannot realistically be qualified at TQL-1, because its output is not deterministic and it has no specification. That leaves the existing rule: **its output must be fully verified as if hand-written.** No regulator offers a lighter path. [secondary/inference]
- **Evidence and vendor positions:**
  - A Georgia Tech study found that *no* tested LLM produced MISRA-compliant C, even when prompted to. [secondary]
  - Axivion keeps its analysis engine free of AI so that it stays qualifiable, and analyses AI-written code exactly as it analyses human code. [secondary: vendor]
  - AdaCore (2026) demonstrates SPARK proof catching corner-case bugs in AI-generated code. [secondary: vendor]
  - The research tool Marmaragan uses an LLM to write SPARK annotations that GNATprove then checks. [primary: arXiv 2502.07728]
- **The emerging pattern is "LLM proposes, a qualified or sound tool disposes".** The generator does not need to be trusted when the checker is sound. The same logic underlies CompCert-style translation validation and DO-330 Criterion 3. [secondary/inference]

## Concept map: safety-critical practice → Decision-First Review

| Safety-critical concept | Analogue in Decision-First Review |
|---|---|
| DAL A–E / ASIL / SIL / IEC 62304 class | LIGHT / STANDARD / DEEP tiers, assigned deterministically from blast radius |
| Objectives "with independence" | AI never signs. Author ≠ signer. DEEP adds a second human reviewer |
| DO-330 tool qualification (TQL) / ISO 26262 TCL | A registry of which tools may emit **PROVEN**. A sound analyser (Astrée-class) qualifies. A linter gives HEURISTIC at most |
| Unqualified tool → output fully verified | Agent-written code gets full verification, with no trust in the generator |
| DO-333 unit proof replacing unit test | PROVEN evidence lets a claim skip line-level review |
| Trace data (bidirectional) | Requirement-linked decision record. Code with no trace is flagged as an "untraced decision" |
| MC/DC / structural coverage analysis | Coverage reconciliation: uncovered changed lines are resolved as a missing test, dead code or a missing requirement |
| SCADE KCG TQL-1 generator | Trusted-generator provenance: generated files skip line review, and the generator's inputs are reviewed instead |
| JPL SCRUB (one queue, every item answered) | A single evidence ledger. Every finding gets an author response and a sign-off |
| Power of 10 (tool-checkable rules) | Policies written as machine-checkable gates, not prose |
| IV&V / DER sign-off | A named human signs and is accountable |

## Slide-quotable items

1. **"Airbus replaced unit testing with formal proof on A380 flight software."** Caveat unit proof covered about 30,000 lines of C, with testing kept only as the fallback for code that could not be proved. Source: Souyris, Delmas et al., ERTS 2006/2008, and "Formal Verification of Avionics Software Products", FM 2009 (di.ens.fr/~delmas/papers/fm09.pdf). [primary]
2. **"Under DO-178C, a tool earns trust only through qualification. Otherwise its output is checked as if a human wrote it."** No regulator yet treats an LLM as a qualifiable code generator. EASA's and the FAA's AI guidance covers AI *in* aircraft, not AI *writing* aircraft code. Sources: RTCA DO-330; EASA AI Concept Paper Issue 02; FAA AI Safety Assurance Roadmap (2024). [primary for scope; the DO-330 rule is secondary, from vendor summaries]
3. **"JPL reviewed Mars Curiosity's flight code by putting human reviewers and static analysers in one queue, and every item needed a written answer."** Source: G. J. Holzmann, "SCRUB: a tool for code reviews", *Innovations in Systems and Software Engineering* 6 (2010) 311–318; NTRS 20100033572. [primary]

### Key URLs
- EASA AI Concept Paper Issue 02: https://www.easa.europa.eu/en/downloads/137631/en
- FAA AI Roadmap: https://www.faa.gov/media/82891
- SCRUB: https://ntrs.nasa.gov/citations/20100033572
- Airbus unit proof: https://www.di.ens.fr/~delmas/papers/fm09.pdf ; https://www.di.ens.fr/~delmas/papers/erts08.pdf
- CompCert/MTU: https://www.absint.com/compcert/mtu_compcert_erts_2018.pdf
- Astrée: https://www.astree.ens.fr/ ; https://www.absint.com/astree/
- SCADE DO-178C handbook: https://www.ansys.com/content/dam/content-creators/creative/source-files/assets-for-mvp/products/embedded/aeronautics-handbook-do-178c-scade-suite.pdf
- NVIDIA SPARK: https://www.adacore.com/case-studies/nvidia-adoption-of-spark-new-era-in-security-critical-software-development
- Line 14 B-method: https://ar5iv.labs.arxiv.org/html/2005.07190
- LLM SPARK annotations: https://arxiv.org/abs/2502.07728
- DAL objective counts: https://www.rapitasystems.com/blog/whats-difference-between-sil-and-dal-how-does-it-affect-my-code-coverage

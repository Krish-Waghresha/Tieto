# Submission Checklist: Earned Trust in AI Code

## Strategy

We are a two-person team. Prioritize the concept, one worked example, and one demonstration format. Do not build a complete product.

The organizers clarified to our team that a working prototype is not expected; original thinking and a credible viability plan are. The written [challenge brief](tieto-challenge.md) still asks for a reference illustration and evidence. Meet that intent with one inspectable, requirement-linked example, clearly distinguishing implemented, manually verified, simulated, and proposed elements.

Suggested allocation of remaining time: 50% concept and walkthrough, 30% sample evidence and viability, 20% submission and rehearsal. This is a team recommendation, not an organizer requirement.

Our working recommendation:

> Use program analysis to identify which review obligations can be checked mechanically, and use an evidence-grounded LLM to explain the behavioral changes and uncertainties that need human judgment. A named engineer owns the final decision.

## Two-Person Work Split

Replace Person A and Person B with our names before starting. These are responsibilities, not separate teams.

| Owner | Primary responsibility | Outputs |
| --- | --- | --- |
| Person A | Concept, reviewer experience, presentation, and submission | Concept card, source-linked visual walkthrough, final deck/recording as required, submitted package |
| Person B | Sample investigation, evidence, technical viability, and measurement plan | Requirement-linked evidence packet, verified finding, unresolved question, architecture and measurement notes |
| Both | Scope decisions, claim checking, lessons log, and rehearsal | Agreed scope, checked presentation claims, human decision record, short shared log |

Work in three passes:

1. Together: choose the requirement and sample, agree the central claim, and sketch the walkthrough. Confirm submission logistics immediately.
2. In parallel: Person B investigates the sample while Person A drafts the concept and walkthrough structure. Use placeholders until evidence is verified; do not invent results to fit the story.
3. Together: connect the visuals to actual evidence, challenge each other's claims, rehearse, and submit. Stop adding features once this pass begins.

Keep the package small: one concept card, one evidence packet, one walkthrough deck, and one short lessons/decisions log. Put architecture and measurement plans in the deck or its appendix; record the same walkthrough if a video is required. The sections below are coverage checks, not separate documents or implementation projects.

## 1. Lock Scope and Ownership

Owner: both. Person A owns logistics; Person B owns sample selection.

- [ ] Put our names against Person A and Person B, and name the engineer responsible for the sample's final review decision.
- [ ] Confirm submission deadline, submission channel, presentation duration, required formats, and whether a recording is required in addition to the live walkthrough.
- [ ] Select one manageable agent-written change and its requirement ID. A small, well-understood change is enough; 2,000 lines are not necessary.
- [ ] Use synthetic or cleared data only. Make our own copy before working with the supplied repository.
- [ ] Record the requirement, expected behavior, base/head revisions, and relevant functional, security, and performance constraints.
- [ ] Use a slide-based before/after flow walkthrough as the default. Add click-through interactions only if needed to inspect evidence. Keep generated podcasts, videos, and quizzes as future extensions, not parallel builds.

## 2. Concept Card: Clarity (30%)

Owner: Person A. Person B checks technical claims and limits.

- [ ] Produce a concise concept card covering recommendation, principles, trade-offs, and limits.
- [ ] Explain the original contribution: evidence-backed reduction of review scope plus targeted help understanding what remains, not merely another AI summary.
- [ ] Define routing within a PR: mechanically checked changes, human-review-required changes, and unknown or unsupported changes. Unknowns require human attention.
- [ ] Explain why line count and apparent simplicity do not determine risk. A one-line authorization change can demand deep review.
- [ ] Distinguish tool-verified claims, test-supported claims, LLM interpretations, and unknowns. Do not collapse these into an unexplained confidence percentage.
- [ ] State that CFGs describe control flow, passing tests cover tested cases, and neither alone proves a change correct.
- [ ] State that AI gives advice, never approval; high-risk changes still receive deep human review.
- [ ] State the main trade-offs: less manual inspection versus missed defects; accessible explanations versus omitted nuance; deeper analysis versus latency and cost.
- [ ] Name limits such as dynamic dispatch, reflection, missing dependencies, incomplete requirements, and unsupported languages or frameworks.

## 3. Worked Example: Evidence (20%)

Owner: Person B. Person A checks whether the evidence is understandable and traceable.

- [ ] Show the requirement and original behavior before presenting the proposed change.
- [ ] Show exactly which review obligations can receive lighter checks, which need deeper review, and why. Do not force a low-risk classification if the sample does not support one.
- [ ] Provide at least one actual AI finding and verify it through source inspection or an executable check. Identify who verified it and how; a full application is not needed.
- [ ] For each material claim, link the requirement, affected code, supporting artifact, and verification method.
- [ ] Show at least one explicit refusal or unresolved question, the missing evidence, and the human action needed to resolve it.
- [ ] Build a before/after behavioral explanation with source references. Distinguish observed execution from statically inferred or illustrative paths.
- [ ] Let the reviewer inspect the underlying evidence instead of relying on the narration alone.
- [ ] Include a human decision record: owner name, requirement ID, reviewed revision, checks and their authors/tools, unchecked scope and reasons, residual risk, decision, and timestamp.
- [ ] Demonstrate that findings or unresolved risks can cause rejection or a request for changes. Do not force approval to complete the story.
- [ ] Label every demo artifact as actually executed, manually verified, simulated, or proposed where applicable. Never present invented analyzer output as real evidence.

## 4. Viability Plan: Practicality (25%)

Owner: Person B. Person A turns the plan into one architecture/workflow slide with supporting notes. Describe these capabilities; do not implement every component.

- [ ] Show the workflow: PR and requirement -> analysis -> evidence-backed routing -> explanation -> human decision -> outcome monitoring.
- [ ] Name concrete candidate tools and their jobs. For a C# sample, consider Roslyn syntax/semantic/CFG analysis, compiler diagnostics, and existing tests; verify capabilities before claiming them.
- [ ] Define the LLM's inputs and role: explain evidence, propose findings for verification, and state uncertainty. It must not turn its own confidence into proof.
- [ ] Address frontend behavior: navigate from claims to source, distinguish uncertainty, inspect evidence, and record a human decision.
- [ ] Address backend behavior: revision-bound analysis jobs, artifact storage, invalidation after new commits, and explicit handling of failed or incomplete checks.
- [ ] Address security: treat repository content as untrusted input, prevent prompt text from overriding review policy, isolate any code execution, and protect secrets and source data.
- [ ] Explain scaling through changed-symbol/dependency analysis, revision-aware caching, and risk-based escalation. Mark performance and cost estimates as estimates.
- [ ] Explain PR integration and reviewer ownership without implementing a full GitHub app. Unsupported analysis must not silently become a pass.
- [ ] Define a rollout: one supported language and narrow check set, shadow reviews alongside normal review, then limited adoption only after measured results.
- [ ] State when trust is withdrawn: stale evidence, missing context, analysis failure, unsupported claims, or an escaped defect. Specify who investigates and restores eligibility for lighter review.

## 5. Measurement Plan (25%)

Owner: Person B. Present a measurement plan, plus any small checks actually completed. Production metrics and a formal user study are not hackathon build requirements. A teammate walkthrough is a comprehension check, not independent evidence of time savings or safety.

- [ ] Define a baseline: the existing human review process on comparable changes, with the same decision task.
- [ ] Define how to measure active human review time separately from end-to-end time to merge.
- [ ] Define how to measure the share of changes requiring deep human review and record the routing reasons.
- [ ] Define how to track verified findings and reviewer acceptance separately. Reviewer acceptance alone does not establish correctness.
- [ ] Define how to track missed defects, reverts, and incidents by affected area and severity, using explicit denominators and observation periods.
- [ ] Plan human spot-checks of changes routed to lighter review, recording false negatives and feeding them back into routing policy.
- [ ] Describe a small pilot that checks whether reviewers find known defects, identify remaining uncertainty, and make the correct decision. Run it only if time and participants permit; do not treat an already-seen example as an unbiased comparison.
- [ ] Separate observed results, targets, estimates, and measurements planned for deployment. Do not claim production safety or time savings from a scripted demo.
- [ ] Define a rollout stop rule and responsible owner, such as a critical escape triggering a pause in lighter review for the affected area.

## 6. Lessons and Decisions Log

Owner: both. Each person adds short entries as decisions or failures occur; no dedicated documentation role is needed.

- [ ] Keep a short log throughout preparation, not only after the presentation is finished.
- [ ] Record important design choices, alternatives, trade-offs, owners, and dates.
- [ ] Record observed failures, supporting evidence, mitigations, and remaining gaps. Separate anticipated failure modes from failures actually observed.
- [ ] Include the risk of a persuasive but incorrect explanation, false reassurance from tests, missed dependencies, and stale evidence after a new commit.
- [ ] Explain why a quiz result or polished narration is not proof of understanding, correctness, or authorization to merge.

Suggested log fields: date | observation or decision | evidence | rationale | owner | next action.

## 7. Walkthrough and Final Submission

Owner: Person A. Person B checks evidence links and technical accuracy; both rehearse and verify the submitted package.

- [ ] Open with the decision problem: a named engineer must approve an AI-written change without blindly trusting it.
- [ ] Introduce the requirement, sample change, and two review paths in plain language.
- [ ] Show a mechanically supported claim, a consequential behavioral change, and the evidence behind the explanation. If a separate illustrative example is needed, label it clearly.
- [ ] Show a finding and an abstention, including what happens next in each case.
- [ ] Show the named human's decision and exactly what responsibility remains with them.
- [ ] Close with the viability plan, measurement plan, trade-offs, and limitations.
- [ ] Prepare concise answers to: "What would make you not trust this?", "Who owns the decision?", "How does it scale?", and "What have you actually demonstrated?"
- [ ] Rehearse within the confirmed time limit and test all evidence links and presentation assets.
- [ ] Prepare an offline walkthrough or recording so network/model availability is not essential to judging.
- [ ] Package the concept card, worked example/evidence, live walkthrough assets, lessons/decisions log, and demo video/presentation in the required submission format.
- [ ] Submit and verify the submitted links, permissions, and confirmation.

## Optional Technical Proof

Owner: Person B, with Person A reusing the outputs in the walkthrough. Only attempt this once the core story and submission artifacts are on track. Agree a time limit first and choose one small proof, not a platform. Stop if it threatens rehearsal or submission; retain honest source-inspection evidence and disclose what was not executed.

- [ ] Run one real analyzer or focused regression check on the sample and retain the command, revision, tool version, output, and limitations.
- [ ] Generate one source-linked explanation from those artifacts with an available partner model, then manually check its material claims.
- [ ] Reuse the resulting evidence in the existing walkthrough. Do not build a second presentation format just for the technical proof.

Do not prioritize production integrations, multi-language coverage, custom static-analysis engines, model training, vendor comparisons, or multiple media generators.

## Ready-to-Submit Test

An unfamiliar engineer should be able to identify the requirement, explain the important behavior change, inspect a supporting artifact, name an uncertainty, and say who owns the decision after the walkthrough. If not, improve the explanation and evidence before adding features.
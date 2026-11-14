> **STATUS: RESEARCH FINDINGS — NOT FINAL.** Collected from web sources and read-only inspection on 2026-11-14. Vendor claims and [UNVERIFIED] items must be checked before use on slides.

# Jane Street on code review, AI-written code and verification

Research date: 2026-11-14. Raw transcripts are in `/tmp/junction-research/js-transcripts/`.

**Note on names:** "Ron Minsky" and "Yaron Minsky" are the same person. He is Jane Street's co-head of technology and hosts Signals and Threads as "Ron".

## Sources (V = I read the full primary text)

| Source | URL | Status |
|---|---|---|
| Ian Henry, "How Jane Street Does Code Review" (2017) | youtube.com/watch?v=MUqvXHEjmus, janestreet.com/tech-talks/janestreet-code-review | V (official transcript, no timestamps) |
| Y. Minsky, "Scrutinizing your code in style" (2014) | blog.janestreet.com/scrutinizing-your-code-in-style | V |
| J. Crepezzi, "AI Engineering at Jane Street" (AI Eng. Summit 2025) | youtube.com/watch?v=0ML7ZLMdcl4 | V (edited transcript with timestamps, from ai.engineer) |
| Signals and Threads ep. 31, "The Changing Craft of Programming" (Crepezzi, 16 Oct 2026) | signalsandthreads.com/the-changing-craft-of-programming | V |
| Signals and Threads ep. 26, "Why Testing is Hard" (Will Wilson, 16 Mar 2026) | signalsandthreads.com/why-testing-is-hard-and-how-to-fix-it | V (timestamped) |
| Y. Minsky, "Formal methods and the future of programming" (7 Jun 2026) | blog.janestreet.com/formal-methods-at-jane-street-index | V |
| J. Somers, "The joy of expect tests" (2023) | blog.janestreet.com/the-joy-of-expect-tests | V |
| R. Minsky, "Now more than ever" (Bug Bash 2026) | youtube.com/watch?v=rUYP4C29yCw | **Abstract only.** No transcript; the automated caption download was denied. |

## 1. Iron mechanics and their AI-review equivalents

- **Ownership metadata.** Files checked into the repo declare "the owner of the file" and "the file scrutiny". Owners also inherit leftover work: unresolved CRs become "CR-soons" assigned to the file owner. *AI mapping:* a named accountable human per path, declared in-repo and machine-readable.
- **Scrutiny levels.** Each scrutiny has a name, a description, the number of required reviewers, and an integer level. Iron "will ask the reviewers to re-review from scratch" if a file's scrutiny goes up. Jane Street found that "no review" outside the critical path was "a mistake… unreviewed parts of the tree turned into swamps". *AI mapping:* risk tiers that set the required human attention. AI-only review is acceptable at low tiers, and human sign-off is mandatory at high ones.
- **n/k obligations.** "Someone needs to look at it from this group, but not necessarily everyone." *AI mapping:* quorum rules that can count an AI reviewer as one of k, but never as the required human.
- **Seconding.** Review follows a sequence: the seconder (a "co-designer") explicitly says "I sign off on this", then review "widens to file reviewers". *AI mapping:* an explicit, attributable human sign-off event, separate from "AI found no issues".
- **Brains and incremental review.** Each person/branch pair has a brain, "a mutable diff" of what that person has actually read. Review is complete when brain = branch, and "You never have to read a commit twice, even after it's rebased." *AI mapping:* record per reviewer, human or AI, exactly which content was attested. When the AI amends code after a human approval, show only the diff since the human's brain, and never carry an approval over to code the human hasn't seen.
- **CRs and XCRs.** Review comments live in the code (`CR author: …`). Replying flips a CR to an XCR "and assigns it back"; comments are "part of the code, so you never lose context". *AI mapping:* AI findings become CRs that a named human must resolve or explicitly defer.
- **Release rules.** "If you haven't fully reviewed a branch, you can't release it… It will not let you release it if you release a feature that has CRs in it." Iron also handles merge cases where a low-scrutiny change hits a code path whose scrutiny has gone up. *AI mapping:* a hard merge gate that the tool enforces, not policy text.

## 2. AI tooling

- **AIDE** is a sidecar service between models and thin editor plugins (Emacs, VS Code, Neovim). It handles context, prompts and build status, makes models swappable, supports A/B testing by acceptance rate, and later grew into the AIDE CLI agent.
- **Training data.** Iron features were too long (500–1,000 lines) and commits were "Summary Z". Instead the team takes **workspace snapshots** about every 20 seconds, together with build status. Green→red→green transitions mark isolated edits; red→green transitions pair an error with its fix. An LLM writes the prompt, which is then shortened.
- **CES (Code Evaluation Service).** Pre-warmed builds apply model diffs and report red or green to the RL reward function. The same setup handles evaluation, using held-out RL data.
- **"I'll do it tomorrow."** After months of training, the code-review model answered its first review with "Mm, I'll do it tomorrow", because it learned from human review threads. Crepezzi's lesson: "having evaluations that are meaningful is kind of a cornerstone".
- **2026 state (ep. 31).** Teams run many LLM code-review systems for bugs, security and regressions, including a multi-agent "review squad". There is a pluggable layer, because review advice "is almost necessarily domain specific". Diffractor reorders diffs into a narrative. LLM graders are themselves evaluated by "meta graders" and broken into rubrics.

## 3. Testing as reviewable evidence

- **Expect tests** capture output inline, and "regressions are just diffs". Behaviour becomes something a reviewer can read in the diff itself.
- **Property tests and fuzzing:** "Tests are incredibly valuable as well, and can be made even better by leaning into property-based tests and fuzzing" (Y. Minsky, 2026).
- **Deterministic simulation (Antithesis).** Failures can be replayed. Its limitation is speed: "you might come back tomorrow to look at the results" (Ron, ep. 26, 01:09:58).
- **Warning about the evaluator itself:** "the more powerful and unyielding the validation step is, probably the worse this overall effect gets" (Will Wilson, 01:17:52). Agents game tests, and "testing while still important just isn't enough" (Ron, 01:19:41).

## 4. The formal-methods turn (Y. Minsky, June 2026)

He wrote: "I've been telling people for the last 25 years that Jane Street… was just not interested in formal methods. I'm not saying that anymore." He gives three reasons why now:

1. Cost fell, because models make proofs cheaper.
2. "The verification bottleneck is more important than ever", since agent code "still tends towards slop".
3. "Agents thrive on feedback", and universal guarantees (the "∀" of type systems) beat sampled tests.

He adds that agents can't build hard proofs alone: "models still need help and guidance from humans". Jane Street is building a formal-methods team in New York and London around OxCaml.

## 5. Quotes for slides (verbatim)

1. "It deliberately stops and forces you to do the right thing." (Ian Henry, MUqvXHEjmus, transcript)
2. "If you haven't fully reviewed a branch, you can't release it." (same)
3. "A brain is a piece of state that's associated with a person/branch pair." (same)
4. "The verification bottleneck is more important than ever." (Y. Minsky, blog, 2026-06-07)
5. "Agentic code is getting better, but is still tends towards slop." (same; grammar is in the original)
6. "I think in some ways it's harder to verify code that no person wrote." (Ron, ep. 31, section 01:20:04)
7. "Human understanding is as critical as ever the whole way through. You can't really trust the models to do any piece of it without you understanding it." (same section)
8. "…the whole existence of AI agents has kind of broken the social contract around code review… now all you need is a prompt and a dream." (Ron, ep. 31, section 01:43:33)
9. "I can have 10 Claude codes all writing code, and it doesn't matter. I'm not going to go any faster if I can't merge those PRs after reviewing them." (Will Wilson, ep. 26, 00:57:12)
10. "Mm, I'll do it tomorrow." (AI reviewer, quoted by Crepezzi, 0ML7ZLMdcl4 at 12:06)
11. "In expect tests, regressions are just diffs." (J. Somers, 2023)

## 6. What Tieto can steal

1. **Obligations file per path:** owner, risk tier (scrutiny), and n/k quorum, stored in the repo and enforced by the gate.
2. **Scrutiny escalation:** raising a path's tier invalidates earlier approvals and forces re-review from scratch.
3. **An attestation "brain" per reviewer.** Store the exact content each human or AI attested. After AI amendments, the human sees only the delta, and approval never covers unseen code.
4. **Sequenced review:** AI first pass → named human seconder (explicit sign-off) → owners of high-tier files. The AI is never the seconder.
5. **AI findings as CRs:** each needs a human resolution (fixed, rejected or CR-soon to the owner) before release, which builds an audit trail of overrides.
6. **An evidence bundle instead of a verdict.** Expect-test diffs, property/fuzz results, type and proof checks, and the agent's session log (Crepezzi's "why did you make that choice" idea) are routed to the human with a narrative ordering of the diff.
7. **Evaluate the reviewer.** Use held-out bugs and meta-graders, and catch "I'll do it tomorrow" failures. Treat agents gaming the gate (Goodhart) as a risk you monitor.
8. **Push back on the merit of a change, not only its correctness.** Treat AI PRs as prototypes ("let's talk about the merit of the change").

## 7. Caveats: what doesn't transfer

- **OCaml and OxCaml.** Strong types do much of the "∀" work, and Jane Street controls the language. Typical stacks (Python, JS) get weaker guarantees for free.
- **A custom centralized tool.** Iron combines version control and review on Mercurial in a single monorepo. GitHub or GitLab need bots and branch protection to imitate it, and diff-of-diff review is hard to bolt on.
- **Culture.** Small branches, senior reviewers, and a firm that pays for heavy review on safety-critical code. Jane Street admits the top tier is "pretty expensive".
- **Proprietary training.** Fine-tuning on workspace snapshots needs scale and data most clients don't have.
- **Unverified source.** The Bug Bash 2026 talk content is known only from its abstract. Don't quote it beyond that.

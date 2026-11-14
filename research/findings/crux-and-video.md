> **STATUS: RESEARCH FINDINGS — NOT FINAL.** Collected from web sources and read-only inspection on 2026-11-14. Vendor claims and [UNVERIFIED] items must be checked before use on slides.

# Crux (kiasm) and the "HTML engineer" video: research notes

Sources fetched on 2026-11-14 are listed at the end. Quotes from Crux come from the live site's HTML. The FAQ answers sit in the Next.js payload because the accordions are collapsed, so a plain WebFetch misses them.

## (a) Crux: what it is and how it works

- **Who makes it:** An alpha product ("v0.12.0", "alpha build") from three cofounders: Dimos Georgellis, Francesco Fantin and Marco Baresi. It was built at DTU Skylab in Copenhagen and is supported by Mikrolegat. "kiasm" seems to be the company or org name; it appears in crux@kiasm.dev, the GitHub org `kiasm/crux-web` and LinkedIn `crux-kiasm`. Its tagline is "Verified code comprehension." There are five design-partner seats.
- **Pitch:** "AI writes your code in minutes. Understanding it still takes weeks." and "Crux reads a real repository and writes short, interactive courses from the code that is actually in it. Then it checks, by asking, that the people shipping that code can explain it."
- **Input:** "Read-only GitHub access, on the branch you pick." You can delete your data at any time. The first course arrives in "about forty seconds."
- **Pipeline:** (1) Connect a repo read-only. (2) "Generate a course per subsystem." (3) Read the course. (4) "Verify by recall, not by reading." (5) "Master the system, measurably."
- **Outputs:**
  - **Courses**, typed as Structure, Concepts, Code or General ("Next.js App Router … as kiasm/crux-web uses it"), with domain tags such as architecture, auth, api, data or testing, "at three depths." Each course states learning goals ("After this course you'll be able to: Say which file renders a given URL…"). It then walks through steps, each showing a real code excerpt with line numbers next to plain-language annotations, then key takeaways and a list of "Files to remember."
  - **Quizzes:** for example, "Put the request path in the order it actually runs." The FAQ says: "order the calls, name what breaks, point at the line that swallows the error."
  - **Mastery heatmap:** comprehension by domain over time.
  - **Read-aloud**, in the free tier. This is the only audio feature.
  - Custom courses on request ("what a new joiner needs to know by Friday").
  - Planned features: "PR-check courses" (Scale tier), manager curation and due dates, team mastery maps, and an undescribed "StarCatch." The landing page shows no flow diagrams or visual graphs.
- **Trust and accuracy:** "every step cites the file it came from, so nothing drifts from the source." Verification is defined like this: "Passing marks that subsystem verified for that person, at that commit, and it expires when the code underneath it moves." The site does not mention hallucination, wrong explanations, abstention, or how quiz answers are checked against the code.
- **Research:** Crux's own survey (n=92, July 2026), of whom 54% were students or interns and only 5 were seniors. Crux flags the sample as unrepresentative. Findings: 61% have shipped code they did not fully understand, 67% go to AI first, only 7.6% trust AI code without review, and the hardest parts are file and function relationships (26%) and architecture and flow (22%). Top wishes are "an AI navigator that explains code with evidence" (32.6%) and visual maps (21.7%). A senior asked to "Explain why design decisions were made." The site cites no learning-science research, although the "recall" design follows the retrieval-practice idea.
- **Pricing:** Free gets 1 person, 1 repo and 3 courses a month. Team, Scale and Org tiers are "coming soon."
- **Public discussion:** I found none on HN, Reddit, Product Hunt or X.

## (b) Video: Qrpm7E80wQ0

- **Metadata:** "Why this Claude Code engineer uses HTML files as AI specs | Thariq Shihipar (Anthropic)." Channel: How I AI (@howiaipodcast), hosted by Claire Vo. Published 2026-05-18 as the episode "HTML is the new Markdown: How Anthropic engineers are building with Claude Code," recorded at Code with Claude.
- **"HTML engineer":** This refers to Thariq, the "Claude Code engineer [who] uses HTML files." He calls himself "probably far on the HTML maximalist side." It is about HTML as the output format, not a job role.
- **Provenance:** Quotes with timestamps come from a third-party auto-transcript (podscripts.co), which has ASR errors such as "Cloud" for Claude. Use cases and prompts come from the speaker's own companion post, "Using Claude Code: The unreasonable effectiveness of HTML" (claude.dev/blog, 2026-05-20), and from his gallery (thariqs.github.io/html-effectiveness). Bullets 7 and 8 (the "1%" and "verification" lines) are from Lenny's and ChatPRD's show notes, and I also confirmed them in the transcript.

**Argument**
1. Long markdown plans no longer get read: "the plans are so long, I honestly have stopped reading them. And this is honestly a mistake… We really need to understand what the agents are doing" (03:28). The post says: "I find it difficult to read a Markdown file of more than a hundred lines."
2. HTML keeps humans in the loop because it is denser (SVG, tables, tabs, mockups, code), easy to share by link, and two-way.
3. Demo (07:00–22:00): he brainstorms 8 ideas as a visual HTML page. Claude then interviews him to surface "unknown unknowns." Next comes an HTML implementation plan ("include excerpts, mockups, code, whatever is needed to give me maximum context"). Last, a throwaway "micro-software" editor for the decision rules, with a copy-back-as-markdown export.
4. **Review boundary:** "the types help me understand what we're building… that's the boundary I want to interface." The "two bookends" are the data model and how to test it.
5. "Verification is not testing": rubrics, managed agents, "have Claude record a video of what it did," and synthetic-data regression runs (16:40).
6. Living HTML design system. HTML status reports are "like a hundred times" more likely to be read.
7. About 1% of the tokens he generates become production code. The rest is understanding and steering artefacts.
8. ChatPRD's caveat: "A beautiful interface can make weak thinking easier to overlook."

**Code comprehension techniques (from the post and gallery)**
- An annotated PR: the real diff with margin notes tagged blocking, nit or nice, plus jump links. Prompt: "I'm not very familiar with the streaming/backpressure logic, so focus on that… color-code findings by severity."
- A **PR writeup for reviewers**: TL;DR, Why, Before/After, a "File-by-file" tour "in reading order" explaining the *why*, "Where to focus your review" with file:line pointers, a test plan, and rollout.
- A **module map**: boxes and arrows, with the hot path highlighted and entry points listed.
- A **feature explainer** ("Optimize it for someone reading it once"): TL;DR, collapsible steps linked to source lines, a files-read list, and a gotchas section.
- A clickable **annotated flowchart** showing failure paths.
- An interactive concept explainer with a live model and a hover glossary.
- Audio and memorisation are not covered. The only "podcast" is the demo topic.
- The post says nothing about hallucination or accuracy.

## (c) Ideas the comprehension layer could adopt, and where the team differs

**Adopt**
- A **per-PR HTML review packet** built on Thariq's PR-writeup structure, with the file tour in reading order, a "where to focus" list, and a before/after flow diagram. Its depth should scale with the light, normal or deep route.
- **Tailoring to reviewer familiarity:** his "I'm not familiar with X, focus on that," combined with Crux's per-person mastery data. This lets the packet expand on areas the named reviewer has not mastered.
- **Recall gating from Crux:** before deep-route approval, give the reviewer 2–3 questions such as "order the calls in the new path" or "which line handles the error." They should be generated from the deterministic call graph so the answer key is provable, not taken from the LLM.
- **Commit-scoped, expiring "verified" state:** the reviewer's sign-off is tied to a commit SHA and invalidated by new pushes.
- **Types and tests as the boundary:** lead with changes to data models and interfaces, and then show the evidence that they are validated.
- **Read-aloud or podcast** as an optional 2-minute summary for light routes.

**How the team differs or improves**
- **Requirement-traced evidence:** every claim (a "why" or a decision) links to a ticket, spec line, or diff hunk, plus a static-analysis fact. Crux cites only files, and Thariq cites nothing systematically.
- **Abstention:** say "Unknown: intent not stated in PR or ticket" instead of inventing a rationale, and route such cases to deep review. Neither source handles hallucination.
- **Accountability:** record the named reviewer, the artefacts they saw, the quiz results and their sign-off in an audit trail. Crux measures understanding for onboarding, not responsibility for a merge.
- **Deterministic first:** the graphs come from the AST and flow analysis, and the LLM only annotates them. Crux and Thariq rely on LLM-drawn diagrams.
- **Per-PR comprehension:** Crux does whole-repo onboarding, with "PR-check courses" only on the roadmap. That is the gap the team can fill.

## (d) Open questions

- Is Crux's "PR-check courses" feature live, and what is StarCatch? Ask crux@kiasm.dev or book the 20-minute demo.
- How does Crux check quiz answers and prevent wrong explanations? The site does not say.
- Does recall gating improve defect detection or only slow reviewers down? Neither source has evidence. Crux's survey is self-selected and junior-heavy.
- Is the full video transcript needed? Podscripts was usable but it is ASR. The main agent may want the official YouTube subtitles to confirm quotes.
- How do you stop polished HTML from creating false confidence, the "beautiful interface" risk? One option is to show confidence and abstention prominently.

## Sources
- https://crux.kiasm.dev/ , /pricing , /about , /survey
- https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v=Qrpm7E80wQ0&format=json
- https://claude.dev/blog/using-claude-code-the-unreasonable-effectiveness-of-html/
- https://thariqs.github.io/html-effectiveness/ (incl. 17-pr-writeup.html)
- https://podscripts.co/podcasts/how-i-ai/html-is-the-new-markdown-how-anthropic-engineers-are-building-with-claude-code-thariq-shihipar
- https://www.lennysnewsletter.com/p/how-i-ai-html-is-the-new-markdown
- https://www.chatprd.ai/how-i-ai/claude-code-anthropic-thariq-shihipar-on-replacing-markdown-with-html

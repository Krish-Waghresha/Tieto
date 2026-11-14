> **STATUS: RESEARCH FINDINGS — NOT FINAL.** Research wave A agent output, 2026-11-14. Items marked [secondary]/[UNVERIFIED] must be checked before use on slides; see fact-check-waveB.md.

# RESEARCH FINDINGS — not final
Wave A: Visualization and comprehension for "Decision-First Review" (compiled 2026-11-14)

Already covered elsewhere, so not repeated here: CodeRabbit, DeepWiki, Crux, Swimm/CodeTour/CodeSee, difftastic/SemanticDiff/GumTree/RAID, Shihipar "HTML is the new markdown", Diffractor.

## 1. Code-graph infrastructure (deterministic layer)

| Tool | Graph type | PR-diff capable? | C# support | Cost/licence | URL |
|---|---|---|---|---|---|
| Joern | Code property graph (AST+CFG+PDG), queried in a Scala DSL | No built-in diff. Build the CPG at both SHAs and diff the method sets | `csharpsrc2cpg` frontend exists (javadoc, v2.0.x), but it isn't in the docs' language table, so maturity is unclear | Apache-2.0 | https://docs.joern.io |
| CodeQL | Relational DB with AST, CFG, data flow and call graph (QL) | `--diff-informed`/PR scanning in Actions. You need two DBs to diff the graphs | Yes (mature) | Free for OSS and research. Private repos need GitHub Code Security | https://codeql.github.com |
| SCIP + scip-dotnet | Symbol occurrences: defs and refs, no CFG | Yes, by indexing base and head and diffing symbols and refs | Yes, Roslyn-based, C# and VB | Apache-2.0 | https://github.com/sourcegraph/scip-dotnet |
| Glean (Meta) | Fact DB per language schema, Angle query language | Supports incremental/stacked DBs | No C# indexer found | BSD | https://engineering.fb.com/2024/12/19/developer-tools/glean-open-source-code-indexing/ |
| Kythe (Google) | Cross-reference graph | No | No C# indexer (C++, Go, Java only) | Apache-2.0 | https://kythe.io |
| OpenRewrite/Moderne LST | Lossless, type-attributed tree | Recipes yield diffs, not graph views | C# LST added May 2026 (NuGet OpenRewrite.CSharp) | OSS core. Moderne platform is commercial | https://docs.moderne.io/user-documentation/moderne-cli/how-to-guides/csharp |
| tree-sitter (+stack-graphs) | Concrete syntax trees. Stack graphs gave name resolution | Fast parsing of both sides | tree-sitter-c-sharp grammar exists. stack-graphs was archived 9 Sep 2025 | MIT | https://github.com/github/stack-graphs |
| Roslyn | Syntax plus semantic model, `ControlFlowGraph.Create`, call info via SymbolFinder | DIY, but it is the most exact option for C# | Native | MIT | https://github.com/dotnet/roslyn |
| NDepend | Dependency graph and matrix, CQLinq | Yes. "Code Diff since Baseline", changed dependencies flagged in the matrix, built-in diff CQLinq rules | Native .NET | Commercial per-seat (about €500/dev per an informal source) | https://www.ndepend.com/features/code-diff |
| VS Code Maps / dependency diagrams | Dependency graph | No | C#/VB | Creating them needs VS Enterprise | https://learn.microsoft.com/visualstudio/modeling/map-dependencies-across-your-solutions |
| SciTools Understand | Call, butterfly and architecture graphs | Yes. Butterfly/Calls *Compare* graphs show added, removed and modified edges against a previous project | Yes | Commercial | https://docs.scitools.com/graphs/Butterfly.html |
| CodeScene | Behavioural graph: hotspots, change coupling from git history | Yes. Code Health PR check, and PR comments flag files that usually change together | Yes | About €18–27 per active author/month (third-party listings) | https://codescene.com |
| GitHub dependency review | Package dependency diff | Yes, but only at package level | NuGet | Part of GHAS for private repos | docs.github.com |

**Takeaway for C#.** The cheapest deterministic route for a hackathon is Roslyn. It gives exact CFGs per changed method, and SymbolFinder gives callers and callees one hop out. scip-dotnet is the portable alternative. Understand's Compare graphs and NDepend's baseline diff show that the "changed subgraph" idea already exists commercially for C#, but only inside desktop tools and never inside the PR.

## 2. LLM + code-graph tools (2025–2026)
- **Greptile.** Indexes the repo into a graph of functions, classes, imports and calls, and adds LLM docstrings per node. On each PR, agents pull in callers and dependencies "beyond the diff". The output can include sequence diagrams and flowcharts. The graph internals are not documented. [primary marketing/docs]
- **Potpie.** Apache-2.0. Neo4j graph of files, classes, functions and call relations, with agents running on top. It now pitches itself as a "context graph" that also stores decisions and history. [primary repo]
- **code-graph-rag (vitali87).** MIT. Tree-sitter feeds a Memgraph graph, which is queried in natural language via Cypher. Runs as an MCP server. [primary repo]
- **Aider repo map.** Tree-sitter extracts definitions and references, builds a file graph, and ranks it with personalized PageRank toward the files in the chat. This is a deterministic way to choose which neighbours to show. [primary, aider.chat 2023]
- **Cursor and Claude Code.** Cursor uses embedding-based codebase indexing. Claude Code uses agentic grep and read, with no persistent index. [UNVERIFIED in this pass]
- **Graphite.** Cursor agreed to acquire it on 19 Dec 2025, and it continues as a standalone product. It handles stacked PRs, which split changes manually, but it has no graph view. Reviewpad's status is unknown. [primary/secondary]
- **PR-impact graphs in research.** ChangeViz (VISSOFT 2021) adds Stacksplorer-style caller/callee panes to the GitHub PR page. ReviewVis (JSS 2023) shows MR change-sets as graphs. ExplorViz (VISSOFT 2024) shows a PR's structural changes plus runtime traces as a software city. **None of these has a product successor. The gap is still open.**

## 3. Research: visualization and untangling in review
- **ClusterChanges** (Barnett, Bird, Brunet, Lahiri, ICSE 2015). Uses def-use relations to partition changesets at Microsoft (Bing, Office). Most developers agreed with the partitioning and said it was useful for reviewers. The tool was never released, but a Java replication from 2018 exists. [primary]
- **di Biase et al., PeerJ CS 2019.** A controlled experiment with 28 developers. Decomposition did **not** increase the number of defects found, but it **reduced wrongly reported issues** (false positives). [primary abstract]
- **CoRA (ASE 2019).** Decomposes tangled changes *and* generates a description for each cluster. This is the closest academic ancestor of "decisions with explanations". [secondary]
- **Baum, Schneider, Bacchelli, EMSE 2019.** No reliable evidence that the order of change parts matters. The firm finding is that small changes get much more effective reviews. [primary]
- **Rahman, Codabux, Roy, ICSE 2026.** Survey of 1,355 developers: only 10.2% consider alphabetical file order optimal, 63.9% worry it makes them miss bugs, and 66% want custom ordering. [primary]
- **Stacksplorer** (call-graph navigation in the IDE, not in review). In a controlled experiment, developers solved more tasks correctly and faster, with more awareness of side effects. [primary]
- **Evidence against or missing.** ReviewVis's own evaluation is perception-only and calls for studies on review effectiveness. I found **no controlled study showing that call-graph diagrams in review increase defect detection**. Expect comprehension and confidence gains, not proven bug-catching. [primary/secondary]

## 4. Explaining code changes
- **PR descriptions written by AI agents** (Gong et al., MSR'26, arXiv 2601.04886). 23,247 agent PRs. The most common inconsistency is **"Phantom Changes" (45.4%)**: the description claims changes that were never made. High-inconsistency PRs had a 28.3% vs 80.0% acceptance rate and took 3.5× longer to merge. [primary]
- **Hallucination in change-to-text** (arXiv 2508.08661). About **50% of generated review comments and about 20% of generated commit messages contain hallucinations**. [primary abstract]
- **Commit messages.** Human raters preferred LLM messages in 78% of 366 samples (SANER 2024). OMG (FSE 2024) argues that the diff alone is not enough context. [primary]
- **HalluJudge (Atlassian, 2026).** A reference-free hallucination detector for review comments: F1 0.85 at about $0.009 per check. This is cheap enough to gate every annotation. [primary abstract]
- **Google.** ML-suggested edits resolve about 7.5% of reviewer comments (ICSE-SEIP 2024). AutoCommenter had about 40% of comments resolved. I found **no public Google paper on ML-generated CL descriptions**. [primary/UNVERIFIED]
- **Microsoft Nudge** (TOSEM 2022/23). Randomized trial on 147 repos and 8,500 PRs: **60.6% shorter PR completion time**, and 73% of notifications were rated positive. It shows that small, targeted interventions in the PR beat big dashboards. [primary]
- **Grounding pattern.** The most robust approach is to let the LLM only label nodes and edges that the deterministic graph produced, and require every claim to cite a node ID or line range. Any claim that does not resolve to the graph is a phantom candidate.

## 5. Comprehension and learning
- **Brooks (1983).** Comprehension is top-down and hypothesis-driven: readers confirm hypotheses through *beacons*, such as a swap inside nested loops signalling a sort. Soloway & Ehrlich (1984) describe experts using *programming plans* and discourse rules. Bottom-up chunking (Pennington) dominates in unfamiliar code. [secondary surveys]
- **Mayer's multimedia principles.** Redundancy principle: median **d = 0.86** across 16/16 comparisons. Do not show on-screen text that duplicates narration. Boundary condition: *slightly* different text can help (Yue, Bjork & Bjork 2013). Signalling and segmenting also apply. [primary/secondary]
- **Audio for code.** In a replication study of code explanations as audio vs text vs both (Zavgorodniaia et al., Aalto 2020), the formats made **no significant difference** to transfer or cognitive load. Practitioner reviews say audio-only coding content fails because code and diagrams are visual. So use audio, if at all, for the "why" of a decision, never to read code aloud. [primary/secondary]
- **Spaced repetition for codebases.** Only tools and anecdotes exist (Anki decks, Code Cards). No studies were found. [secondary]

## What to take for the comprehension layer
1. **One decision = one cluster.** Partition the PR ClusterChanges-style using def-use and call edges from Roslyn or SCIP. Cite di Biase et al.: fewer false positives.
2. **Show only the changed subgraph plus one hop.** Draw changed nodes filled, untouched callers and callees hollow. Use Understand's Compare encoding: added green, removed red, modified amber.
3. **Rank which neighbours to show** with personalized PageRank seeded on the changed symbols, as Aider does. This keeps the graph to 7–12 nodes.
4. **Order the cards by dependency, not alphabet.** Show callees before callers, or the entry point first (ICSE 2026 survey).
5. **Mark beacons.** Highlight the single line per decision that confirms the hypothesis (the guard, the new branch), following Brooks.
6. **Before/after CFG for one method only.** Show it side by side with Roslyn's `ControlFlowGraph`, and only for a decision whose branch structure changed.
7. **Every LLM sentence must cite a node ID or line range.** Unresolvable claims get flagged as "phantom" and are counted against Gong's 45% baseline.
8. **Follow the redundancy principle.** The graph carries the structure and the text carries only the *why*. Don't restate edges in prose.
9. **Add a CodeScene-style change-coupling hint**: "files that usually change with this one but didn't". This is cheap to compute from git log.
10. **Keep the in-PR card minimal, as Nudge did**, and link out to the HTML view for depth.

## Slide-quotable
- "45.4% of inconsistencies in AI-agent PR descriptions are *phantom changes*: claims about code that was never written." (Gong et al., MSR 2026)
- "Only 10.2% of 1,355 reviewers think alphabetical file order is optimal, yet it's the default everywhere." (Rahman et al., ICSE 2026)
- "Splitting a tangled change didn't help reviewers find more bugs, but it cut false alarms." (di Biase et al., 2019)

## Confidence marks
- [primary]: Nudge numbers, Gong PR-MCI numbers, ICSE 2026 survey, Baum 2019, Barnett 2015 framing, NDepend/Understand/SciTools diff features, scip-dotnet, stack-graphs archive date, Moderne C# date, Aider repo map, Mayer d=0.86 table.
- [secondary]: di Biase exact defect result (abstract fragments only), CodeScene pricing, Greptile internals, Joern C# maturity, Glean language list, CoRA details, Soloway dates.
- [UNVERIFIED]: Cursor/Claude Code indexing details, Google ML-generated CL descriptions (nothing found), Reviewpad status, NDepend price, ChangeViz/ReviewVis quantitative results.

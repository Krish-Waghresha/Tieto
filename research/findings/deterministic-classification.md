> **STATUS: RESEARCH FINDINGS — NOT FINAL.** Collected from web sources and read-only inspection on 2026-11-14. Vendor claims and [UNVERIFIED] items must be checked before use on slides.

> **CORRECTION (verified 2026-11-14):** Commit `32258fdb` (PolySharp bump + Roslyn 4.3→4.12) is a dependabot commit from 2025-03-01 and the repo default branch — the shared *base* of all four ju26 branches, NOT part of the agent change. The agent change is only `9df83c38`. This report diffed against the wrong base (`524fd55e`). Logged as an observed failure mode: wrong base revision → misattributed changes.

# Deterministic PR classification before any LLM (light / normal / deep)

## 1. Proving change type (equivalence), not guessing
| Claim | Proof technique | What it proves | What it cannot prove |
|---|---|---|---|
| formatting-only | Parse both sides with Roslyn and compare `SyntaxTree.IsEquivalentTo(other, topLevel:false)` (ignores trivia). Or compare emitted IL with deterministic build (`/deterministic`) | Token streams identical, so compiled semantics identical | Nothing missing. This is a real proof |
| docs/test-only | Path classifier: every changed file is `*.md`, `doc/**`, or in a test project (from `.csproj` graph, not just the folder name) | Shipped assemblies unchanged (confirm: product DLL bytes identical under deterministic build) | Whether the tests got weaker (see signals) |
| rename-only | Roslyn: map old to new symbols. Equal after alpha-renaming, and `SymbolFinder.FindReferencesAsync` shows every reference updated. AST diff (GumTree, https://github.com/GumTreeDiff/gumtree; difftastic, https://difftastic.wilfred.me.uk/) labels edits as *update-identifier* only | Private renames preserve behaviour | Public renames break API/binary compat. Reflection or serialization by name (MessagePack `[Key("name")]`, string keys) can change wire format |
| pure refactor | RefactoringMiner (Java, https://github.com/tsantalis/RefactoringMiner); RefactoringMiner++ for C++ (https://arxiv.org/abs/2502.17716); RefDetect (multi-language, IEEE Access 2021, not publicly released). **No maintained C# port exists.** | Suggests a refactoring with roughly 87-99% precision | Behaviour preservation. Detection is not verification |
| API surface unchanged | `Microsoft.CodeAnalysis.PublicApiAnalyzers` (RS0016/RS0017 vs `PublicAPI.Shipped/Unshipped.txt`); `Microsoft.DotNet.ApiCompat` / package validation | The public contract is unchanged, or the exact delta | Behaviour behind the API |
| generator output unchanged | Re-run the ~90 golden-output test cases (`tests/MessagePack.SourceGenerator.Tests/Resources`, 90 dirs / 226 files) and compare byte for byte | **For those inputs** the generated code is identical. This is differential testing against a frozen oracle | Untested inputs. Analyzer diagnostics (not part of the golden files). Runtime behaviour |
| semantic equivalence | Regression verification (Godlin & Strichman, 2009/2013), symbolic equivalence (e.g. ARDiff) | Equivalence for loop-bounded code | Does not scale to Roslyn-sized code. Not practical at a hackathon |

Rule: a label is **proven** only when it comes from a sound check (trivia-only AST equality, identical deterministic binaries, empty API diff, identical golden output). Any other label is **heuristic** and the report must say so.

## 2. Blast radius
- **In-solution (exact):** open the solution with `MSBuildWorkspace`. Map diff hunks to their enclosing symbols (`SemanticModel.GetDeclaredSymbol`). Then call `SymbolFinder.FindReferencesAsync`, `FindCallersAsync`, `FindDerivedClassesAsync` and `FindImplementationsAsync` transitively. The output is a list of affected symbols, each with a file:line. That gives a checkable "touches X, Y" claim. It is sound for static calls and misses reflection and DI.
- **Intra-method:** `ControlFlowGraph.Create(IMethodBodyOperation)` (Microsoft.CodeAnalysis.FlowAnalysis) on old and new code. Diff the basic blocks and branch conditions to flag "new branch / new early return / swallowed path".
- **Data flow / taint:** CodeQL C# databases (`build-mode: none` works without a build but is less accurate: https://docs.github.com/en/code-security/reference/code-scanning/codeql/build-options-for-compiled-languages). Use `DataFlow::` path queries from changed sources to sinks.
- **Cross-repo indexes:** SCIP/scip-dotnet (Sourcegraph), Glean (Meta), Kythe (Google). GitHub's stack-graphs was archived in Sep 2025, so don't build on it. All of these are overkill for one repo. Roslyn already gives exact answers here.
- **Test impact:** run coverage (coverlet/`dotnet-coverage`) on the base branch to get a symbol→tests map. Changed symbols then select their tests. Report it as "N tests cover the changed lines; M of them are new".

## 3. Risk signals with evidence
- **JIT defect prediction**, Kamei et al., TSE 2013 (https://sail.cs.queensu.ca/data/pdfs/TSE_ALarge-ScaleEmpiricalStudyOfJust-in-TimeQualityAssurance.pdf). Four groups: size (LA, LD, LT), diffusion (NS, ND, NF, entropy), history (NDEV, AGE, NUC), experience (EXP, REXP, SEXP). The evidence is strongest for **size/churn (relative churn LA/LT)** and **diffusion**. Fix commits and files with a past bug history also predict defects. Experience adds little. The models reach about 68% accuracy and 64% recall, so treat these as priors and never as verdicts.
- **Hotspots** (CodeScene / Tornhill): churn × complexity per file. **Ownership** (Bird et al., FSE 2011): a minor-contributor ratio correlates with defects.
- **Domain rules** (deterministic, no empirical score needed, mark them "policy"): touches serialization, formatter resolution, `unsafe`, reflection/`Emit`, crypto, concurrency, public API delta, package or version changes in `Directory.Packages.props`, deleted or weakened tests (fewer `Assert`, added `Skip`, golden file rewritten in the same PR as the generator).
- **Explainability:** score = Σ rule points. Each line of the output reads `RULE-ID | evidence (file:line / metric value) | +points`. Tier thresholds are fixed and versioned. Any single *hard* rule (public API break, dependency change in an analyzer, golden files edited together with generator code) forces at least **deep**, whatever the sum.

## 4. Static analysis for C# (cheap, SARIF)
- Built-in .NET SDK analyzers (`AnalysisLevel=latest-all`): CA2100 SQL, CA5350/5351 weak crypto, CA2300-2330 insecure deserializers (relevant for a serializer). `<ErrorLog>file.sarif</ErrorLog>` emits SARIF during the normal build, so the extra cost is close to zero.
- `Microsoft.CodeAnalysis.Analyzers` for generators: RS1035 (banned APIs in analyzers, e.g. file IO), RS1036, RS2008 (release tracking). Also `BannedApiAnalyzers` (RS0030) and `PublicApiAnalyzers`. Nullable reference types (CS86xx) as warnings-as-errors on changed files.
- SonarAnalyzer.CSharp (NuGet, runs in the build). Semgrep C# rules (fast, no build, SARIF). CodeQL C# (minutes, SARIF, strongest for taint). Security Code Scan: only the `.VS2019` package is current, and GitLab dropped it in 16.0. Infer# (microsoft/infersharp): stale since about 2024, so skip it.
- Diff-scope everything: report only findings on changed lines, and compare base vs head SARIF to get *new* findings.

## 5. Confidence without fake percentages
- Use three evidence grades: **PROVEN** (sound check passed), **MEASURED** (deterministic fact such as "3 hard rules fired", "fan-in 34 call sites"), and **HEURISTIC** (statistical prior).
- Calibrate tiers on history. Replay the classifier over the repo's past merged PRs and label the outcomes: reverted, followed by a fix within N days (SZZ), or attracted review change requests. Report **precision-at-tier** ("of 120 historical *light* PRs, 2 needed a follow-up fix") instead of a per-PR probability.
- Use **selective classification / conformal prediction** (Angelopoulos & Bates, https://arxiv.org/abs/2107.07511) for routing. Route to *light* only if the conformal prediction set is {light}. Any ambiguous set escalates. Abstaining is cheap, while under-reviewing is expensive.

## 6. Pipeline for MessagePack-CSharp
1. `git diff` classification: docs / tests / product / build (PROVEN by path + project graph).
2. Trivia-insensitive AST equality per file, giving formatting-only (PROVEN).
3. `dotnet build -warnaserror` with SARIF from the NetAnalyzers, Microsoft.CodeAnalysis.Analyzers (RS1035) and PublicApiAnalyzers. Report new findings only.
4. Package diff of `Directory.Packages.props` (MEASURED). An analyzer-project dependency change is a hard rule.
5. Roslyn symbol mapping plus `FindReferences`/callers for blast radius. CFG diff of the changed methods.
6. Golden-output run of `MessagePack.SourceGenerator.Tests`: generated code identical? (PROVEN for 90 inputs). Hard rule if `Resources/**` changed.
7. Test-impact: covering tests, new tests, assertion count delta.
8. Semgrep/CodeQL with diff-scoping (deep tier, or always if CI time allows).
9. Score → tier, with a rule trace.

**Tiers.** *Light*: PROVEN docs, test-only or formatting-only, no new findings. *Normal*: product code with local blast radius, golden output unchanged, no hard rule, tests added. *Deep*: any hard rule. Examples are a public API or dependency change, generator output or golden-file change, a change in diagnostic/serialization semantics with high fan-in, or new analyzer findings.

### ju26-issue-2283 → **DEEP** (verified against the branch's actual diff)
Diff vs merge-base `524fd55e`: 5 files, +227/−5. `TypeCollector.cs` +29, `GenericsFormatterTests.cs` +189 (3 new `[Fact]`s for closed generics from metadata references), `README.md` and `doc/analyzers/MsgPack004.md` +5 each, `Directory.Packages.props` 2 lines.

Rule trace:
- **HARD: analyzer dependency change.** The branch carries commit `32258fdb`, which bumps PolySharp 1.14.1→1.15.0 *and* raises `MicrosoftCodeAnalysisVersion` for `IsAnalyzerProject` from **4.3.0 to 4.12.0**. That raises the minimum compiler/VS version that can load the generator, which is a consumer compatibility change hidden inside a "fix" PR.
- **HARD: diagnostic semantics with high fan-in.** The constructor now wraps `reportDiagnostic` in `ReportIfLocatedInCompilation`. That filters **all 34 `reportDiagnostic` call sites**, not only MsgPack004. Any diagnostic whose location is `null`/`Location.None` (e.g. `GetIdentifierLocation(...)` returning null, line ~405, 1211, 1324) or lies in metadata (e.g. MsgPack003 `formattedType.Locations[0]` at ~1345 when `callerSymbol` is null) is now **silently dropped**. A CFG diff shows a new conditional early exit on every reporting path.
- **MEASURED, mitigating:** the null-safe `FirstOrDefault()` and `as` replace a hard cast and `[0]` indexing (they remove a crash). There are 3 new tests and the docs are consistent with the change.
- **PROVEN (if green):** the golden outputs are unchanged, so generated *code* is identical for the 90 inputs. This says nothing about the *diagnostics*, which is exactly what changed. Golden equality therefore cannot downgrade this PR.

Reviewer questions to generate: Is dropping `Location.None` diagnostics intended? Should the Roslyn 4.3→4.12 bump be in this PR at all? Add a test asserting that in-source MsgPack003/MsgPack004 diagnostics are still reported.

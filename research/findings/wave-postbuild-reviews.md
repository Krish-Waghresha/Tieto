> **STATUS: RESEARCH FINDINGS — NOT FINAL.** Two independent review agents ran against the first end-to-end demo (PR #1 on the `demo/*` branches), 2026-11-14. Fixes were applied in commit "Harden demo after security and judge reviews" on `demo/base`.

# Post-build reviews of the demo

## Security / correctness review (reproduced = R, traced = T)

| # | Severity | Issue | Status |
| --- | --- | --- | --- |
| 1 | Critical (T) | `pull_request` / `pull_request_review` run workflow files from the PR — a PR could edit the pipeline to approve itself | Review moved to `pull_request_target` (base workflow, bot, policy, proof script, pinned SHAs; PR files as data). **Sign path remains a documented limitation** (GitHub runs `pull_request_review` from the merge ref; production needs a GitHub App / default-branch workflow) |
| 2 | Critical (T) | Proof script and pinned upstream SHAs came from the PR head → forgeable evidence | Script and SHAs from base; provenance reads PR files via `git show` |
| 3 | Critical (R) | Triage only diffed `sample/` → PRs touching `.github/**` or `review-policy.json` could be LIGHT | Whole-repo diff; regression test `test_workflow_change_is_deep` |
| 4 | Critical (T) | Any GitHub user could sign | `author_association` must be OWNER/MEMBER/COLLABORATOR |
| 5 | Critical (R) | `python3 -c` from PR checkout root with write token → code execution via a planted `json.py` | No PR checkout in privileged jobs; `jq` + base-revision bot |
| 6 | High (R) | Timeout / NotExecuted outcomes and missing facts counted as pass | Unknown outcomes → UNSUPPORTED; missing facts never hold |
| 7 | High (R) | Empty/binary diffs LIGHT; whitespace inside strings and YAML indentation treated as cosmetic | LIGHT needs textual hunks; indentation-sensitive files never cosmetic |
| 8 | High (R) | Markdown injection into bot replies via `/sign` text | All repo/user text escaped (links, mentions, issue refs, HTML, newlines) |
| 9 | High (R) | `head: 1` accepted; duplicate keys last-wins; ledger pin unchecked | Exact 40-char head; duplicates rejected; ledger head + PR checked |
| 10 | Medium (T) | Stale ledger from older run could be used | Artifacts named by head SHA; newest by name |
| 11 | Medium (T) | Head-commit pushers and machine-user agents could sign | Excluded; agent account deny-list in policy |

## Judge review (Tieto persona) — main points

- **Failed the 60-second test** on "what does the change do" and "who owns the decision" → added a plain-language summary, the bot's read, and a named owner at the top.
- **Jargon** (hunk, ledger, PROVEN/ARGUED) → plain labels: *checked by tool, test result, tool estimate, AI reasoning (unverified), AI won't decide, not run*.
- **Mixed counts** → "Checks run: X of Y" shown first and separately.
- **Contradictions found** (P0 mentioned but absent; quiz key labels; "3 questions" vs 4; mixed units in scope check; README overclaimed execution) → all fixed.
- **Unreachable report** (private repo, no Pages) → rendered `REPORT.md` on branch `demo/reports` linked from the comment; HTML downloadable.
- **Single best addition:** execute P1, P2, P4b, P4h so finding F1 is confirmed or disproved by a real test → blocked on GitHub Actions being enabled, or local Docker.

## Lesson

The reviewer of AI code needs the same treatment we propose for AI code: adversarial review, regression tests for every finding, and honest labels for what is not fixed.

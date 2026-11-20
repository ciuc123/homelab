# SEO / AI-search audit: client deliverable kit

How to turn a `seo_audit` run into a report a client can act on without a call. The tool covers what can be checked automatically from outside. This kit adds the checks that need a human or account access, a grading rubric and the report layout.

| File | What it is |
|---|---|
| [rubric.md](rubric.md) | How the score becomes five area grades, and how findings are prioritized |
| [manual-checklist.md](manual-checklist.md) | Checks the tool can't do (speed after load, analytics, hosting quirks, content, off-site entity), with how to check each |
| [report-template.md](report-template.md) | The client-facing report: summary, area grades, top fixes, 30/60/90 plan, re-audit |

## Process

1. **Run the automated audit.**
   - Homelab: open a "SEO audit" issue with the client's URL. The full report lands in `audits/<host>/<date>.md` and `.json`.
   - Locally: `python3 seo_audit audit-url https://client.example --max-pages 100 --json a.json --markdown a.md`.
   - ⚠ `ciuc123/homelab` is public, so issues, comments and committed reports are public too. Until that's decided, run client audits locally and keep the files out of the public repo.
2. **Grade it.** Map the results to the five areas in [rubric.md](rubric.md).
3. **Do the manual checklist.** Each item gets ✅, ❌ or "n/a" and one line of evidence: a command output, a screenshot path or a number.
4. **Write the report** from [report-template.md](report-template.md). Keep the client's language: no rule IDs in the summary, at most five top fixes, and every fix with a "why it matters" and a "how".
5. **Re-audit** 4–8 weeks after the fixes. The automated part compares with `--previous a.json`; repeat the manual checklist too. The before/after pair is the case study.

## Principles

- **Numbers or it didn't happen.** Every finding has evidence, and every "after" is measured the same way as its "before".
- **Impact first.** Lost leads and indexing come first, how the site appears in search and AI answers second, polish last.
- **Honest about limits.** Say what wasn't checked, for example "no Search Console access, so no query data".

# Rubric

## Five areas

Each automated rule belongs to one area. Manual checks (see [manual-checklist.md](manual-checklist.md)) add to the same areas.

| Area | What a client hears | Automated rules | Key manual checks |
|---|---|---|---|
| **1. Leads & conversion** | "Can interested visitors reach you?" | `form-action`, `post-cta` | M1 form end to end, M2 analytics events |
| **2. Findability (crawl & index)** | "Can search engines and AI crawlers find every page?" | `robots-txt`, `sitemap`, `sitemap-urls-exist`, `ai-search-crawlers`, `canonical`, `not-found-page`, `internal-links`, `orphan-pages`, `private-files` | M5 hosting paths, M6 redirects, M7 Search Console coverage |
| **3. Search appearance** | "What do people see before they click?" | `single-title`, `meta-description`, `meta-description-length`, `og-image`, `single-h1`, `img-alt` (+ `title-length`, `description-*`, `tags-present`, `stale-year-in-title` with source access) | M8 real snippets, M9 share preview |
| **4. AI answers & entity** | "Do AI assistants know who you are and quote you?" | `entity-schema`, `json-ld-present`, `json-ld-valid`, `article-author`, `faq-schema-valid`, `llms-txt` (+ `post-tldr`, `question-heading`, `sources-section`, `faq-entries` with source access) | M10 AI panel, M11 off-site profiles |
| **5. Speed & weight** | "How fast does it feel on a phone?" | none (manual) | M3 Lighthouse ×3, M4 weight after load |

## Area grade

For automated rules: **pass rate = passed checks ÷ all checks in the area.**

| Grade | Pass rate | And |
|---|---|---|
| **A** | ≥ 98% | no failing rule at impact 1, no ❌ on a manual check in the area |
| **B** | ≥ 90% | at most one impact-1 rule failing |
| **C** | ≥ 75% | — |
| **D** | < 75% | or any lead-loss finding (form that doesn't deliver, site-wide noindex, robots blocking all) |

The manual checks can lower a grade by one step per ❌ but never raise it. Area 5 is graded on manual checks only:
- **A:** Lighthouse mobile median ≥ 90 and ≤ 500 KB at 10 s.
- **B:** ≥ 75 and ≤ 1 MB.
- **C:** ≥ 50.
- **D:** below that.

The overall `seo_audit` score (0–100) stays in the report as the single tracking number. The grades are what the summary talks about.

## Prioritizing fixes

Order: the **impact** tier from `guidance.py` (1 = lost visitors, leads or indexing; 2 = how the site shows up; 3 = polish), then **reach** (how many pages fail), then **effort** (an hour, a day, a project).

The **top five** in the summary are the five highest in that order, with one exception: a manual finding that loses leads (M1) always goes first.

## Evidence rules

- Automated: the rule ID, the failing count and up to three example URLs (the tool's "Where").
- Manual: the command and its output, a screenshot path, or a measured number with its date and method.
- Speed: always the median of three runs, mobile, with the tool and its version. A single Lighthouse run is not evidence.

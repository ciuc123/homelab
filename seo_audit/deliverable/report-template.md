# SEO & AI-search audit: {{Client name}}

**Site:** {{https://client.example}} · **Date:** {{YYYY-MM-DD}} · **Prepared by:** {{name}}
**Scope:** {{N}} pages checked automatically (seo_audit {{version}}) + manual checks M1–M13 · **Not checked:** {{e.g. Search Console, no access}}

---

## Summary

{{Three to five sentences, no jargon. What works, what's costing visitors or leads today, and the one thing to do first.}}

| Area | Grade | In one line |
|---|---|---|
| Leads & conversion | {{A–D}} | {{e.g. "The contact form works, but no analytics event records a lead."}} |
| Findability | {{A–D}} | |
| Search appearance | {{A–D}} | |
| AI answers & entity | {{A–D}} | |
| Speed & weight | {{A–D}} | |

**Tracking score:** {{NN}}/100 ({{passed}} of {{checks}} automated checks pass). Use this number to compare later audits.

## Fix these first

{{Top 5, ordered by the rubric. Each one:}}

### 1. {{Plain-language title, e.g. "Every inquiry from the contact form is lost"}}
- **Why it matters:** {{one or two sentences, in business terms}}
- **Evidence:** {{count + up to three examples, or the measurement}}
- **How to fix:** {{concrete steps}} · **Effort:** {{hour / day / project}} · **Owner:** {{developer / marketing / hosting}}

### 2. …

## 30 / 60 / 90 days

| When | What | Expected effect |
|---|---|---|
| First 30 days | {{the top 5 fixes}} | {{e.g. leads tracked, all pages indexable}} |
| 60 days | {{impact-2 fixes: snippets, structured data, share images, internal links}} | {{better click-through, eligible for rich results and AI citations}} |
| 90 days | {{content: answer-first rewrites of the top pages, a new page per service, off-site profiles}} | {{more queries ranked, mentioned in AI answers}} |

## Measurements

**Speed (mobile, median of 3 runs, Lighthouse {{version}}):**

| Page | Score | First paint | Largest paint | Blocking time | Weight at load | Weight at 10 s |
|---|---|---|---|---|---|---|
| Home | | | | | | |
| {{top landing page}} | | | | | | |
| {{article}} | | | | | | |

**AI answers (M10):** {{x}} of {{y}} answers mention {{Client}}, {{z}} cite the site. Competitors named most often: {{…}}. Brand answers accurate: {{yes/no, what's wrong}}.

## All findings

### Automated
{{Paste "What to fix first" and the "All checks" table from the seo_audit Markdown report.}}

### Manual
| # | Check | Result | Evidence |
|---|---|---|---|
| M1 | Contact form delivers | | |
| M2 | Analytics records leads | | |
| M3 | Lighthouse ×3 | | |
| M4 | Weight after load | | |
| M5 | Hosting-specific paths | | |
| M6 | Redirects | | |
| M7 | Search Console / Bing coverage | | |
| M8 | Real snippets | | |
| M9 | Share preview | | |
| M10 | AI panel | | |
| M11 | Off-site entity | | |
| M12 | Thin and stale content | | |
| M13 | Answer-first | | |

## Re-audit

Recommended on {{date, 4–8 weeks after the fixes}}: the same automated run (`--previous` shows the change per rule), the same manual checks, and the same pages and method for speed. Results go into a before/after table at the top of this report.

## Method

seo_audit is an open-source, dependency-free checker (37 rules: crawlability, metadata, structured data, AI-crawler access, links, conversion basics). The manual checks follow a fixed checklist. All measurements are reproducible: commands and versions are listed in each finding.

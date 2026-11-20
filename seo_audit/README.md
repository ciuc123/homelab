# seo_audit

A dependency-free (Python 3.8+ standard library only) SEO / AEO / GEO audit. It lives in `ciuc123/homelab`:
the **SEO audit** issue form runs it against any live site (see the homelab README), and ciuculescu.com's CI
runs it on every push and pull request, pinned to a `seo-audit-v*` tag.

## Modes

```bash
# Front matter and body rules for Jekyll posts
python3 seo_audit lint-content _posts

# Rendered HTML of a built site (plus the posts, in one report)
bundle exec jekyll build
python3 seo_audit audit-site _site --posts _posts

# A live site, discovered through robots.txt / sitemap.xml (client mode)
python3 seo_audit audit-url https://example.com --max-pages 50 --markdown report.md
```

Every mode takes `--json FILE` and `--markdown FILE` for reports, `--summary FILE` for a short Markdown
summary (the issue comment), `--title` (e.g. the client's name), `--previous FILE.json` to show what changed
since an earlier audit, `--report-url` to link the full report from the summary, and `--quiet` to skip the
console summary. The exit code is 1 if any rule at `error` severity fails, 2 for a config problem, else 0.

**Score** = share of active checks that pass, 0–100. A check is one rule applied to one target (a
page, a post, or the site). Rules set to `off` don't count.

## What to fix first

The Markdown report and the summary list failing rules in order of impact, each with why it matters and
how to fix it in plain language (`guidance.py`): 1 = lost visitors, leads or indexing; 2 = how the site
shows up in search, social and AI answers; 3 = polish. Within a tier, more failures come first.

## Rules

| Rule | Checks |
|---|---|
| `front-matter` | Post has parseable front matter with title and date |
| `title-length` | Post title ≤ 60 characters |
| `description-present` / `description-length` | Post has a description of 120–160 characters |
| `tags-present` | Post has at least one tag |
| `date-matches-filename` | Front matter date = filename date |
| `no-future-date` | Post isn't dated in the future |
| `stale-year-in-title` | Title doesn't name a year older than the post (versions like `2025.1` are fine) |
| `min-word-count` | Body has ≥ `min_words` words, code excluded |
| `last-modified` | `last_modified_at`, if set, is between the post date and today |
| `post-tldr` | *Post standard:* 3–5 key takeaways in `tldr` |
| `faq-entries` | *Post standard:* each `faq` entry is a question ending in `?` with a 20+ word answer |
| `question-heading` | *Post standard:* at least one `##`/`###` heading phrased as a question |
| `sources-section` | *Post standard:* a `## Sources` (or References) section |
| `single-title` | Exactly one `<title>` |
| `meta-description` / `meta-description-length` | Meta description present, 50–160 characters |
| `canonical` | Absolute canonical URL |
| `single-h1` | Exactly one `<h1>` |
| `json-ld-present` / `json-ld-valid` | Structured data present and parseable |
| `faq-schema-valid` | FAQPage JSON-LD has Questions with a name and an accepted answer |
| `og-image` | `og:image` present |
| `img-alt` | Every `<img>` has `alt` |
| `internal-links` | Internal links resolve |
| `post-cta` | Every post (`/posts/YYYY-MM-DD-…/`) has a `.post-cta` block |
| `form-action` | Every `<form>` has a real `action` |
| `robots-txt` | robots.txt exists with a `Sitemap:` line |
| `sitemap` / `sitemap-urls-exist` | sitemap.xml parses and every URL resolves |
| `llms-txt` | llms.txt exists |
| `private-files` | Repo files (README.md, scripts, tools/, workers/…) aren't published |
| `orphan-pages` | Every sitemap page is linked from another page |
| `entity-schema` | The home page has Person/Organization JSON-LD with a name and `sameAs` profile links |
| `article-author` | Every Article/BlogPosting in JSON-LD has an author (name or `@id`) |
| `not-found-page` | A helpful 404 page exists; live: a missing URL returns status 404, not 200 (soft 404) |
| `ai-search-crawlers` | robots.txt doesn't block search engines or AI answer crawlers (blocking training-only crawlers is fine) |

## Config and the ratchet

`.seo-audit.json` at the repo root:

```json
{
  "base_url": "https://ciuculescu.com",
  "min_words": 300,
  "severity": { "og-image": "warning" }
}
```

- `severity` overrides a rule's default (`error`) with `warning` or `off` for `lint-content` and
  `audit-site`. `url_severity` does the same for `audit-url`.
- **Ratchet:** rules that failed on the first baseline start as `warning`, so CI passes while the
  site is fixed. When a task fixes a rule, delete its line. It becomes an `error`, and CI blocks
  any regression from then on.
- `standard_since` (YYYY-MM-DD): posts dated on or after it must follow the answer-first post standard
  (*Post standard* rules above). Without it, those rules don't run.
- Optional: `skip_pages` and `private_files` (glob lists) for `audit-site`, `probe_private` (paths)
  for `audit-url`.

## Tests

```bash
python3 -m unittest discover -s seo_audit/tests
```

The fixtures in `tests/fixtures/` are a good site and posts that pass every rule, and a bad site
and posts that fail each rule at least once. `audit-url` is tested against the fixtures served by a
local HTTP server.

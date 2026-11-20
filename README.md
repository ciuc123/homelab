# homelab

Control plane for client sites. It holds the issue form, the workflow, the secrets and the client registry. The provisioning code lives in the private repo `infra-template`; this repo only calls it.

New here? The step-by-step is in `infra-template/docs/QUICKSTART.md` (private repo).

## Start a client

1. Open an issue with the **New client site** form (client name, subdomain, template, toggles, owner email). Tick **Dry run** first: the workflow comments the plan and creates nothing.
2. Open it again without Dry run. The workflow (`.github/workflows/provision-client.yml`) runs `python -m infra provision`: GitHub repo from the template, Neon database, Vercel project and env vars, Cloudflare DNS (DNS-only until Vercel verifies it), migrations, first deploy. It comments the log on the issue and commits `clients/<name>.json`.
3. Do the Clerk checklist printed at the end (Clerk application creation is manual).

Without an issue: Actions -> Provision client site -> Run workflow, paste a `client.json`.

Only issues opened by the repository owner run anything.

**Dev version**: tick "Dev version" in the form (or `"dev_enabled": true` in the spec) and the run also provisions `dev.<domain>`: a `development` branch in the client repo served as a Vercel branch domain. Push to `development` to update dev, merge to `main` to update production. Details (including the dev database) in the infra-template README.

## Audit a site (SEO, AI search, conversion basics)

1. Open an issue with the **SEO audit** form: target site (required), max pages, client name (optional).
2. The workflow (`.github/workflows/seo-audit.yml`) checks the request (a public http(s) site only), runs `seo_audit audit-url` over the pages in the site's sitemap, and comments a summary on the issue: score, and what to fix first with why and how.
3. The full report is committed to `audits/<host>/<date>.md` (+ `.json`). Re-audit by opening a new issue: the report shows the score change since the last audit of that site.

Without an issue: Actions -> SEO audit -> Run workflow, with the URL. Only issues opened by the repository owner run anything. **This repo is public, so audits are too.**

The same tool gates ciuculescu.com's CI (`ciuc123.github.io`, `.github/workflows/seo-checks.yml`), pinned to a `seo-audit-v*` tag of this repo. Details: `seo_audit/README.md`.

## Secrets (Settings -> Secrets and variables -> Actions)

See `.env.example`: `CF_API_TOKEN`, `CF_ZONE_ID`, `CF_ZONE_NAME`, `VERCEL_TOKEN`, `VERCEL_TEAM_ID` (optional), `NEON_API_KEY`, `GH_PAT`, `NPM_TOKEN`, `CLERK_PLATFORM_API_KEY` (optional).

`scripts/setup-secrets.sh` sets them all in one sitting: per key it prints the page to create it on and the scopes, reads the value from 1Password (item `homelab <KEY>`, field `credential`) or a hidden paste, and pushes it with `gh secret set`. Rotation = update 1Password, re-run. Never paste a secret into a workflow input or an issue: both are stored readably in the run/issue history. These secrets live only here — client repos get their `NPM_TOKEN` from the provisioning run itself.

## Layout

| Path | What |
|---|---|
| `.github/ISSUE_TEMPLATE/new-client.yml` | the issue form |
| `.github/workflows/provision-client.yml` | issue/dispatch -> infra-template |
| `scripts/issue_to_spec.py` | issue form body -> `client.json` (tested in `tests/`) |
| `scripts/setup-secrets.sh` | guided setup of the Actions secrets (1Password or hidden paste -> `gh secret set`) |
| `.github/ISSUE_TEMPLATE/seo-audit.yml` | the SEO audit form |
| `.github/workflows/seo-audit.yml` | issue/dispatch -> `seo_audit audit-url` -> comment + `audits/` |
| `scripts/issue_to_audit.py` | SEO audit form body -> validated target (tested in `tests/`) |
| `seo_audit/` | the audit tool (stdlib Python, own tests in `seo_audit/tests/`) |
| `audits/` | audit reports, one folder per site |
| `clients/` | the registry, one file per client |
| (sales material) | moved to the private `pfa` repo: `sales/` and `projects/client-sites/` |

The old GitHub Pages subdomain script was removed: it could not host this stack, and its DNS wait timed out because it created the CNAME proxied (see infra-template README).

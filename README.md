# homelab

Control plane for client sites. It holds the issue form, the workflow, the secrets and the client registry. The provisioning code lives in the private repo `infra-template`; this repo only calls it.

## Start a client

1. Open an issue with the **New client site** form (client name, subdomain, template, toggles, owner email). Tick **Dry run** first: the workflow comments the plan and creates nothing.
2. Open it again without Dry run. The workflow (`.github/workflows/provision-client.yml`) runs `python -m infra provision`: GitHub repo from the template, Neon database, Vercel project and env vars, Cloudflare DNS (DNS-only until Vercel verifies it), migrations, first deploy. It comments the log on the issue and commits `clients/<name>.json`.
3. Do the Clerk checklist printed at the end (Clerk application creation is manual).

Without an issue: Actions -> Provision client site -> Run workflow, paste a `client.json`.

Only issues opened by the repository owner run anything.

## Secrets (Settings -> Secrets and variables -> Actions)

See `.env.example`: `CF_API_TOKEN`, `CF_ZONE_ID`, `CF_ZONE_NAME`, `VERCEL_TOKEN`, `VERCEL_TEAM_ID` (optional), `NEON_API_KEY`, `GH_PAT`, `NPM_TOKEN`.

## Layout

| Path | What |
|---|---|
| `.github/ISSUE_TEMPLATE/new-client.yml` | the issue form |
| `.github/workflows/provision-client.yml` | issue/dispatch -> infra-template |
| `scripts/issue_to_spec.py` | issue form body -> `client.json` (tested in `tests/`) |
| `clients/` | the registry, one file per client |
| (sales material) | moved to the private `pfa` repo: `sales/` and `projects/client-sites/` |

The old GitHub Pages subdomain script was removed: it could not host this stack, and its DNS wait timed out because it created the CNAME proxied (see infra-template README).

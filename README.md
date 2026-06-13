Create Subdomain Workflow
=========================

Overview
--------
This project provides an automated GitHub Actions workflow and a helper script (scripts/create_subdomain.py) that creates a GitHub repository and configures a custom subdomain on GitHub Pages using Cloudflare DNS. It accepts a new GitHub Issue in a repository and, when the issue body requests a subdomain, it:

- Validates the requested subdomain (only subdomains of the configured zone are allowed; apex domain is rejected).
- Creates a repo (from a template if provided, otherwise scaffolds a minimal static site).
- Publishes the repo as public and enables GitHub Pages.
- Adds a custom domain to Pages and creates the CNAME DNS record in Cloudflare.
- Waits for DNS propagation and for GitHub Pages to verify the domain, then comments on the issue with the URLs.

Usage
-----
Local testing (use .env to provide credentials):

1. Copy .env.example to .env and fill values (do NOT commit .env).
2. Run:
   python scripts/create_subdomain.py --issue-body "subdomain: blog.ciuculescu.com\nrepo: my-blog"

GitHub Actions
--------------
- Create an issue in the repo following the issue format (see below). The workflow triggers on new issues.

Issue body format
-----------------
Use the GitHub issue template **Create subdomain site** to open a pre-filled issue that matches the parser.

Include at least:

subdomain: blog.ciuculescu.com
repo: my-blog

Optional: template: <template_repo_name>

Environment and Secrets
-----------------------
Required repository secrets (set under GitHub repo → Settings → Secrets and variables → Actions):

- CF_API_TOKEN: Cloudflare API token with DNS edit permissions. Create in Cloudflare Dashboard → My Profile → API Tokens; use the "Edit zone DNS" template or grant Zone.Zone (read) + Zone.DNS (edit).
- CF_ZONE_ID: Cloudflare Zone ID for your domain (Dashboard → Overview).
- CF_ZONE_NAME: Zone name (e.g. ciuculescu.com).
- GH_PAT: GitHub Personal Access Token with repo scope (and org permissions if creating repos in an organization).
- GH_OWNER: GitHub user or organization that will own created repositories.

Optional:
- TEMPLATE_REPO, TEMPLATE_OWNER — when provided, the script attempts to generate the new repo from that template; otherwise a minimal site is scaffolded.

Local .env
----------
For convenience the script loads .env (project root) first and uses values there before falling back to environment variables. Use .env only for local testing; it is added to .gitignore.

Security notes
--------------
- Never commit real secrets to the repository. Use GitHub Secrets for CI.
- The script will only create subdomains under the configured CF_ZONE_NAME; it will reject the apex domain.

Troubleshooting
---------------
- If GitHub does not verify the domain immediately, the workflow reports a warning; certificate issuance can take several minutes.
- If DNS propagation times out, check Cloudflare DNS record settings and that CF_API_TOKEN has correct permissions.

Contact
-------
For changes or improvements, open an issue or a PR in this repository.

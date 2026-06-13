This repository contains automation to create a GitHub Pages site for a subdomain and wire up Cloudflare DNS.

What this template provides
- An issues-driven workflow (already present) that will create a site when the repository owner opens an Issue.
- A manual workflow (`manual-create-subdomain.yml`) that lets you run the same flow from the Actions -> Workflows -> Run workflow UI.

Quick setup
1. Add the required repository secrets in Settings → Secrets & variables → Actions:
   - CF_API_TOKEN: Cloudflare API token with DNS edit privileges
   - CF_ZONE_ID: Cloudflare Zone ID (numeric/uuid)
   - CF_ZONE_NAME: The zone name (example.com)
   - GH_PAT: A GitHub token with repo and pages permissions (can be a personal access token)
   - GH_OWNER: The target GitHub owner (your username or organization)
   - (optional) TEMPLATE_OWNER: Owner of a repo template to generate sites from
   - (optional) TEMPLATE_REPO: Name of the template repo (used by the issues workflow)

Using the workflow from the GitHub web interface
1. Push this repository to GitHub.
2. (Optional) Mark the repository as a template: Repository → Settings → Make this repository a template.
   - If you mark it as a template people can click the "Use this template" button to create new repositories pre-populated with these files.
3. Open the Actions tab → select "Create subdomain (manual)" → Click "Run workflow".
4. Fill the inputs (subdomain is required). The workflow will read credentials from the repository secrets and run `scripts/create_subdomain.py`.

Notes
- The manual workflow uses `workflow_dispatch` so maintainers (or anyone with workflow run permissions) can trigger it from the UI.
- The existing `create-subdomain.yml` listens to Issues being opened by the repository owner; keep it if you want that behavior.
- Ensure the secrets are configured before running the workflow; missing secrets will cause the job to fail with a helpful error.

If you'd like, I can also add a tiny issue template that pre-populates the issue body with the keys the script understands (subdomain, repo, template), or a README snippet you can show users when they use the template. Tell me which and I'll add it.


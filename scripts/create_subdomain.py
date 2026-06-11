#!/usr/bin/env python3
import os
import sys
import time
import argparse
import base64
import requests
import dns.resolver

GH_API = 'https://api.github.com'
CF_API = 'https://api.cloudflare.com/client/v4'

def die(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)

def parse_issue_text(text):
    data = {}
    if not text:
        return data
    for line in text.splitlines():
        if ':' in line:
            k, v = line.split(':', 1)
            data[k.strip().lower()] = v.strip()
    return data

# ── Cloudflare helpers ───────────────────────────────────────────────────────

def cf_get_zone(cf_token, zone_id):
    h = {'Authorization': f'Bearer {cf_token}', 'Content-Type': 'application/json'}
    r = requests.get(f'{CF_API}/zones/{zone_id}', headers=h, timeout=20)
    if r.status_code != 200:
        die(f'Cloudflare zone lookup failed: {r.status_code} {r.text}')
    return r.json()['result']

def cf_create_dns(cf_token, zone_id, name, record_type, content, ttl=120, proxied=False):
    h = {'Authorization': f'Bearer {cf_token}', 'Content-Type': 'application/json'}
    payload = {'type': record_type, 'name': name, 'content': content, 'ttl': ttl, 'proxied': proxied}
    r = requests.post(f'{CF_API}/zones/{zone_id}/dns_records', json=payload, headers=h, timeout=20)
    if r.status_code not in (200, 201):
        die(f'Failed creating DNS record: {r.status_code} {r.text}')
    return r.json()['result']

# ── GitHub helpers ───────────────────────────────────────────────────────────

def gh_request(gh_pat, method, url, **kwargs):
    # Caller-supplied headers take precedence over defaults (e.g. preview Accept headers)
    defaults = {'Authorization': f'token {gh_pat}', 'Accept': 'application/vnd.github+json'}
    extra = kwargs.pop('headers', {})
    merged = {**defaults, **extra}
    return requests.request(method, url, headers=merged, timeout=30, **kwargs)

def gh_get_authenticated_user(gh_pat):
    r = gh_request(gh_pat, 'GET', f'{GH_API}/user')
    if r.status_code != 200:
        die(f'Failed to get authenticated user: {r.status_code} {r.text}')
    return r.json().get('login')

def gh_repo_exists(gh_pat, owner, repo):
    r = gh_request(gh_pat, 'GET', f'{GH_API}/repos/{owner}/{repo}')
    return r.status_code == 200

def gh_create_repo_from_template(gh_pat, template_owner, template_repo, owner, name, private=False):
    url = f'{GH_API}/repos/{template_owner}/{template_repo}/generate'
    payload = {'owner': owner, 'name': name, 'private': private}
    # Preview Accept header for the template API - must take precedence over default
    r = gh_request(gh_pat, 'POST', url, json=payload,
                   headers={'Accept': 'application/vnd.github.baptiste-preview+json'})
    if r.status_code in (201, 202):
        return r.json()
    return None  # caller falls back to minimal site

def gh_create_repo(gh_pat, owner, repo, private=False, description=''):
    # auto_init=True creates the default branch so the Contents API works immediately
    payload = {'name': repo, 'private': private, 'description': description, 'auto_init': True}
    authenticated_user = gh_get_authenticated_user(gh_pat)
    if owner.lower() == authenticated_user.lower():
        # Personal account repo
        r = gh_request(gh_pat, 'POST', f'{GH_API}/user/repos', json=payload)
    else:
        # Org repo
        r = gh_request(gh_pat, 'POST', f'{GH_API}/orgs/{owner}/repos', json=payload)
    if r.status_code not in (201, 202):
        die(f'Failed to create repo: {r.status_code} {r.text}')
    return r.json()

def gh_set_repo_public(gh_pat, owner, repo):
    r = gh_request(gh_pat, 'PATCH', f'{GH_API}/repos/{owner}/{repo}', json={'private': False})
    if r.status_code >= 400:
        die(f'Failed to set repo public: {r.status_code} {r.text}')
    return r.json()

def gh_create_file(gh_pat, owner, repo, path, content, message='Add file', branch='main'):
    url = f'{GH_API}/repos/{owner}/{repo}/contents/{path}'
    b64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    payload = {'message': message, 'content': b64, 'branch': branch}
    # If the file already exists (e.g. README.md from auto_init), include its sha to update it
    existing = gh_request(gh_pat, 'GET', url)
    if existing.status_code == 200:
        payload['sha'] = existing.json()['sha']
    r = gh_request(gh_pat, 'PUT', url, json=payload)
    if r.status_code not in (200, 201):
        die(f'Failed creating file {path}: {r.status_code} {r.text}')
    return r.json()

def gh_enable_pages(gh_pat, owner, repo, branch='main'):
    """Create GitHub Pages site via POST, then set custom domain via PUT."""
    url = f'{GH_API}/repos/{owner}/{repo}/pages'
    # POST creates the site; build_type=legacy uses the source branch directly
    r = gh_request(gh_pat, 'POST', url, json={'source': {'branch': branch, 'path': '/'}, 'build_type': 'legacy'})
    if r.status_code not in (200, 201):
        die(f'Failed to enable GitHub Pages: {r.status_code} {r.text}')
    return r.json()

def gh_set_pages_cname(gh_pat, owner, repo, cname):
    """Set (or update) the custom domain for an existing Pages site."""
    url = f'{GH_API}/repos/{owner}/{repo}/pages'
    r = gh_request(gh_pat, 'PUT', url, json={'cname': cname})
    # 204 No Content on success
    if r.status_code not in (200, 204):
        die(f'Failed to set Pages custom domain: {r.status_code} {r.text}')

def gh_get_pages(gh_pat, owner, repo):
    r = gh_request(gh_pat, 'GET', f'{GH_API}/repos/{owner}/{repo}/pages')
    if r.status_code == 404:
        return None
    if r.status_code >= 400:
        die(f'Failed getting Pages info: {r.status_code} {r.text}')
    return r.json()

def post_issue_comment(gh_pat, repo_full, issue_number, body):
    url = f'{GH_API}/repos/{repo_full}/issues/{issue_number}/comments'
    r = gh_request(gh_pat, 'POST', url, json={'body': body})
    if r.status_code >= 400:
        print(f'Warning: failed posting issue comment: {r.status_code} {r.text}')

# ── Name helpers ─────────────────────────────────────────────────────────────

def find_available_repo_name(gh_pat, owner, base):
    candidate = base
    for suffix in range(1, 100):
        if not gh_repo_exists(gh_pat, owner, candidate):
            return candidate
        candidate = f'{base}-{suffix}'
    die('Unable to find an available repo name after 99 attempts')

def create_minimal_site(gh_pat, owner, repo, subdomain, branch='main'):
    index_html = (
        f'<html><head><meta charset="utf-8"><title>{subdomain}</title></head>'
        f'<body><h1>{subdomain}</h1><p>Site generated automatically.</p></body></html>'
    )
    gh_create_file(gh_pat, owner, repo, 'index.html', index_html, 'Create minimal site', branch)
    gh_create_file(gh_pat, owner, repo, 'README.md',
                   f'# {repo}\n\nAuto-generated site for {subdomain}\n',
                   'Add README', branch)

# ── DNS helpers ──────────────────────────────────────────────────────────────

def dns_cname_resolves_to(target, name, attempts=20, wait=15):
    for _ in range(attempts):
        try:
            ans = dns.resolver.resolve(name, 'CNAME')
            for record in ans:
                if target.rstrip('.') in str(record.target):
                    return True
        except Exception:
            pass
        time.sleep(wait)
    return False

# ── .env loader ──────────────────────────────────────────────────────────────

def load_local_env(path='.env'):
    env = {}
    try:
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    k, v = line.split('=', 1)
                    env[k.strip()] = v.strip()
    except FileNotFoundError:
        pass
    return env

# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--issue-title', default='')
    p.add_argument('--issue-body', default='')
    p.add_argument('--subdomain')
    p.add_argument('--repo-name')
    args = p.parse_args()

    local_env = load_local_env()

    def get_env(key):
        # Local .env takes precedence; fall back to process environment (GitHub Secrets)
        return local_env.get(key) if key in local_env else os.environ.get(key)

    cf_token       = get_env('CF_API_TOKEN')
    cf_zone_id     = get_env('CF_ZONE_ID')
    cf_zone_name   = get_env('CF_ZONE_NAME')
    gh_pat         = get_env('GH_PAT')
    gh_owner       = get_env('GH_OWNER')
    template_repo  = get_env('TEMPLATE_REPO') or ''   # optional
    template_owner = get_env('TEMPLATE_OWNER') or get_env('GITHUB_ACTOR') or ''
    issue_number   = get_env('ISSUE_NUMBER')
    issue_repo     = get_env('ISSUE_REPO')

    if not all([cf_token, cf_zone_id, cf_zone_name, gh_pat, gh_owner]):
        die('Missing required env vars: CF_API_TOKEN, CF_ZONE_ID, CF_ZONE_NAME, GH_PAT, GH_OWNER')

    # Parse issue body (passed via env var in CI to avoid shell injection)
    params = parse_issue_text(args.issue_body)
    subdomain  = args.subdomain  or params.get('subdomain') or params.get('domain')
    repo_name  = args.repo_name  or params.get('repo')      or params.get('repo_name') or params.get('repository')
    tmpl_issue = params.get('template')
    if tmpl_issue and not template_repo:
        template_repo = tmpl_issue

    if not subdomain:
        die('Missing subdomain. Add to issue body: subdomain: blog.ciuculescu.com')

    # Default repo name to leftmost label of subdomain
    if not repo_name:
        repo_name = subdomain.split('.', 1)[0]

    # Validate subdomain belongs to configured zone and is not the apex
    if not subdomain.endswith(cf_zone_name):
        die(f'Subdomain {subdomain!r} is not in zone {cf_zone_name!r}')
    if subdomain.rstrip('.') == cf_zone_name.rstrip('.'):
        die(f'{subdomain!r} is the zone apex. Only subdomains are accepted (e.g. blog.{cf_zone_name})')

    # ── Verify Cloudflare zone ───────────────────────────────────────────────
    print('Verifying Cloudflare zone...')
    cf_get_zone(cf_token, cf_zone_id)

    # ── Create GitHub repo ───────────────────────────────────────────────────
    created_repo = None
    chosen_repo_name = repo_name

    if template_repo:
        print(f'Generating repo from template {template_owner}/{template_repo} → {gh_owner}/{repo_name}...')
        created_repo = gh_create_repo_from_template(
            gh_pat, template_owner, template_repo, gh_owner, repo_name, private=False)
        if not created_repo:
            print('Template not found or generation failed; falling back to minimal site.')

    if not created_repo:
        chosen_repo_name = find_available_repo_name(gh_pat, gh_owner, repo_name)
        if chosen_repo_name != repo_name:
            print(f'Repo {repo_name!r} already exists; using {chosen_repo_name!r} instead.')
        print(f'Creating repository {gh_owner}/{chosen_repo_name}...')
        created_repo = gh_create_repo(gh_pat, gh_owner, chosen_repo_name, private=False,
                                      description=f'Auto-generated site for {subdomain}')
        print('Scaffolding minimal site...')
        try:
            create_minimal_site(gh_pat, gh_owner, chosen_repo_name, subdomain, branch='main')
        except Exception as e:
            die(f'Failed to scaffold site files: {e}')

    gh_set_repo_public(gh_pat, gh_owner, chosen_repo_name)

    # ── Enable GitHub Pages ──────────────────────────────────────────────────
    print('Enabling GitHub Pages...')
    gh_enable_pages(gh_pat, gh_owner, chosen_repo_name, branch='main')

    print(f'Setting custom domain {subdomain!r} on Pages...')
    gh_set_pages_cname(gh_pat, gh_owner, chosen_repo_name, subdomain)

    # ── Create Cloudflare DNS CNAME ──────────────────────────────────────────
    target = f'{gh_owner}.github.io'
    print(f'Creating DNS CNAME {subdomain} → {target}...')
    cf_create_dns(cf_token, cf_zone_id, subdomain, 'CNAME', target, ttl=120, proxied=False)

    # ── Wait for DNS propagation ─────────────────────────────────────────────
    print('Waiting for DNS propagation (up to 5 minutes)...')
    if not dns_cname_resolves_to(target, subdomain, attempts=20, wait=15):
        die('DNS did not propagate within timeout. Check Cloudflare settings.')

    # ── Wait for GitHub Pages to go active ───────────────────────────────────
    print('DNS propagated. Waiting for GitHub Pages to become active...')
    for _ in range(40):
        pages = gh_get_pages(gh_pat, gh_owner, chosen_repo_name)
        if pages and pages.get('status') in ('built', 'active'):
            print('Pages is active.')
            break
        time.sleep(15)
    else:
        print('Warning: Pages did not report active within timeout; it may still come up shortly.')

    # ── Done ─────────────────────────────────────────────────────────────────
    site_url  = f'https://{subdomain}'
    repo_url  = created_repo.get('html_url')
    msg = (
        f'✅ Done!\n\n'
        f'**Repository:** {repo_url}\n'
        f'**Site:** {site_url}\n\n'
        f'DNS is propagated. If HTTPS is not yet active, allow a few minutes for the TLS certificate to be issued.'
    )
    print(msg)

    if issue_repo and issue_number:
        post_issue_comment(gh_pat, issue_repo, issue_number, msg)


if __name__ == '__main__':
    main()

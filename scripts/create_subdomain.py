#!/usr/bin/env python3
import os
import sys
import time
import argparse
import json
import re
import requests
import dns.resolver
import base64

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
            k,v = line.split(':',1)
            data[k.strip().lower()] = v.strip()
    return data

# Cloudflare helpers
def cf_get_zone(cf_token, zone_id):
    h = {'Authorization': f'Bearer {cf_token}', 'Content-Type':'application/json'}
    r = requests.get(f'{CF_API}/zones/{zone_id}', headers=h, timeout=20)
    if r.status_code!=200:
        die(f'Cloudflare zone lookup failed: {r.status_code} {r.text}')
    return r.json()['result']

def cf_create_dns(cf_token, zone_id, name, record_type, content, ttl=120, proxied=False):
    h = {'Authorization': f'Bearer {cf_token}', 'Content-Type':'application/json'}
    payload = {'type': record_type, 'name': name, 'content': content, 'ttl': ttl, 'proxied': proxied}
    r = requests.post(f'{CF_API}/zones/{zone_id}/dns_records', json=payload, headers=h, timeout=20)
    if r.status_code not in (200,201):
        die(f'Failed creating DNS record: {r.status_code} {r.text}')
    return r.json()['result']

# GitHub helpers
def gh_request(gh_pat, method, url, **kwargs):
    h = kwargs.pop('headers', {})
    h.update({'Authorization': f'token {gh_pat}', 'Accept':'application/vnd.github+json'})
    return requests.request(method, url, headers=h, timeout=30, **kwargs)

def gh_repo_exists(gh_pat, owner, repo):
    url = f'{GH_API}/repos/{owner}/{repo}'
    r = gh_request(gh_pat, 'GET', url)
    return r.status_code == 200

def gh_get_authenticated_user(gh_pat):
    r = gh_request(gh_pat, 'GET', f'{GH_API}/user')
    if r.status_code!=200:
        die(f'Failed to get authenticated user: {r.status_code} {r.text}')
    return r.json().get('login')

def gh_create_repo_from_template(gh_pat, template_owner, template_repo, owner, name, private=False):
    url = f'{GH_API}/repos/{template_owner}/{template_repo}/generate'
    payload = {'owner': owner, 'name': name, 'private': private}
    r = gh_request(gh_pat, 'POST', url, json=payload, headers={'Accept':'application/vnd.github.baptiste-preview+json'})
    if r.status_code in (201,202):
        return r.json()
    # If template generate fails, return None to fallback
    return None

def gh_create_repo(gh_pat, owner, repo, private=False, description=''):
    # Try org create first
    payload = {'name': repo, 'private': private, 'description': description, 'auto_init': False}
    url_org = f'{GH_API}/orgs/{owner}/repos'
    r = gh_request(gh_pat, 'POST', url_org, json=payload)
    if r.status_code == 201:
        return r.json()
    # If org create forbidden or not found, create under authenticated user
    user = gh_get_authenticated_user(gh_pat)
    url_user = f'{GH_API}/user/repos'
    payload['name'] = repo
    r2 = gh_request(gh_pat, 'POST', url_user, json=payload)
    if r2.status_code in (201,202):
        return r2.json()
    die(f'Failed to create repo: {r.status_code} {r.text} / {r2.status_code} {r2.text}')

def gh_set_repo_public(gh_pat, owner, repo):
    url = f'{GH_API}/repos/{owner}/{repo}'
    r = gh_request(gh_pat, 'PATCH', url, json={'private': False})
    if r.status_code>=400:
        die(f'Failed to set repo public: {r.status_code} {r.text}')
    return r.json()

def gh_create_file(gh_pat, owner, repo, path, content, message='Add file', branch='main'):
    url = f'{GH_API}/repos/{owner}/{repo}/contents/{path}'
    b64 = base64.b64encode(content.encode('utf-8')).decode('utf-8')
    payload = {'message': message, 'content': b64, 'branch': branch}
    r = gh_request(gh_pat, 'PUT', url, json=payload)
    if r.status_code not in (201,200):
        die(f'Failed creating file {path}: {r.status_code} {r.text}')
    return r.json()

def gh_create_pages(gh_pat, owner, repo, branch='main', path='/'):
    url = f'{GH_API}/repos/{owner}/{repo}/pages'
    payload = {'source':{'branch': branch, 'path': path}}
    r = gh_request(gh_pat, 'PUT', url, json=payload)
    if r.status_code not in (201,200):
        die(f'Failed to create pages site: {r.status_code} {r.text}')
    return r.json()

def gh_create_pages_domain(gh_pat, owner, repo, domain):
    url = f'{GH_API}/repos/{owner}/{repo}/pages/domains'
    r = gh_request(gh_pat, 'POST', url, json={'domain': domain})
    if r.status_code not in (201,200):
        die(f'Failed to create pages domain: {r.status_code} {r.text}')
    return r.json()

def gh_get_pages_domain(gh_pat, owner, repo, domain):
    url = f'{GH_API}/repos/{owner}/{repo}/pages/domains/{domain}'
    r = gh_request(gh_pat, 'GET', url)
    if r.status_code==404:
        return None
    if r.status_code>=400:
        die(f'Failed getting pages domain: {r.status_code} {r.text}')
    return r.json()

# DNS helpers
def dns_cname_resolves_to(target, name, attempts=20, wait=15):
    for i in range(attempts):
        try:
            ans = dns.resolver.resolve(name, 'CNAME')
            for r in ans:
                if target.rstrip('.') in str(r.target):
                    return True
        except Exception:
            pass
        time.sleep(wait)
    return False

# GitHub issue comment
def post_issue_comment(gh_pat, repo_full, issue_number, body):
    url = f'{GH_API}/repos/{repo_full}/issues/{issue_number}/comments'
    r = gh_request(gh_pat, 'POST', url, json={'body': body})
    if r.status_code>=400:
        print(f'Warning: failed posting issue comment: {r.status_code} {r.text}')

# Helper to find an available repo name if collision
def find_available_repo_name(gh_pat, owner, base):
    candidate = base
    suffix = 1
    while gh_repo_exists(gh_pat, owner, candidate):
        candidate = f"{base}-{suffix}"
        suffix += 1
        if suffix > 99:
            die('Unable to find available repo name after 99 attempts')
    return candidate

def create_minimal_site(gh_pat, owner, repo, subdomain, branch='main'):
    index_html = f"""<html><head><meta charset=\"utf-8\"><title>{subdomain}</title></head><body><h1>{subdomain}</h1><p>Site generated automatically.</p></body></html>"""
    gh_create_file(gh_pat, owner, repo, 'index.html', index_html, message='Create minimal site', branch=branch)
    # Create README
    gh_create_file(gh_pat, owner, repo, 'README.md', f'# {repo}\n\nAuto-generated site for {subdomain}', message='Add README', branch=branch)

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--issue-title', default='')
    p.add_argument('--issue-body', default='')
    p.add_argument('--subdomain')
    p.add_argument('--repo-name')
    args = p.parse_args()

    env = os.environ
    cf_token = env.get('CF_API_TOKEN')
    cf_zone_id = env.get('CF_ZONE_ID')
    cf_zone_name = env.get('CF_ZONE_NAME')
    gh_pat = env.get('GH_PAT')
    template_owner = env.get('TEMPLATE_OWNER') or env.get('GITHUB_ACTOR')
    template_repo = env.get('TEMPLATE_REPO')  # optional
    gh_owner = env.get('GH_OWNER')
    issue_number = env.get('ISSUE_NUMBER')
    issue_repo = env.get('ISSUE_REPO')

    if not all([cf_token, cf_zone_id, cf_zone_name, gh_pat, gh_owner]):
        die('Missing required environment variables. Set CF_API_TOKEN, CF_ZONE_ID, CF_ZONE_NAME, GH_PAT, GH_OWNER (TEMPLATE_REPO optional)')

    params = parse_issue_text(args.issue_body)
    subdomain = args.subdomain or params.get('subdomain') or params.get('domain')
    repo_name = args.repo_name or params.get('repo') or params.get('repo_name') or params.get('repository')
    template_from_issue = params.get('template') or None
    if template_from_issue and not template_repo:
        template_repo = template_from_issue

    if not subdomain:
        die('Missing subdomain. Provide in issue body like:\nsubdomain: blog.ciuculescu.com')

    # If repo not provided, default to subdomain's leftmost label
    if not repo_name:
        repo_name = subdomain.split('.',1)[0]

    if not subdomain.endswith(cf_zone_name):
        die(f'Subdomain {subdomain} is not in zone {cf_zone_name}')
    if subdomain.rstrip('.') == cf_zone_name.rstrip('.'):
        die(f'Subdomain {subdomain} is the zone apex; only subdomains are allowed. Provide e.g. blog.{cf_zone_name}')

    print('Verifying Cloudflare zone...')
    zone = cf_get_zone(cf_token, cf_zone_id)

    # Decide how to create repo: from template if provided and available, else create minimal site
    created_repo = None
    chosen_repo_name = repo_name

    if template_repo:
        print(f'Attempting to generate repo from template {template_owner}/{template_repo} -> {gh_owner}/{repo_name}...')
        gen = gh_create_repo_from_template(gh_pat, template_owner, template_repo, gh_owner, repo_name, private=False)
        if gen:
            created_repo = gen
        else:
            print('Template generate failed or template missing; will create repo and scaffold minimal site')

    if not created_repo:
        # find available repo name if collision
        chosen_repo_name = find_available_repo_name(gh_pat, gh_owner, repo_name)
        if chosen_repo_name != repo_name:
            print(f'Repo name {repo_name} exists; using {chosen_repo_name} instead')
        print(f'Creating repository {gh_owner}/{chosen_repo_name}...')
        created_repo = gh_create_repo(gh_pat, gh_owner, chosen_repo_name, private=False, description=f'Auto-generated site for {subdomain}')
        # scaffold minimal site
        try:
            create_minimal_site(gh_pat, gh_owner, chosen_repo_name, subdomain, branch='main')
        except Exception as e:
            print('Warning: failed to scaffold files via contents API:', e)

    # Ensure repo public
    gh_set_repo_public(gh_pat, gh_owner, chosen_repo_name)

    # Configure Pages
    try:
        print('Configuring GitHub Pages...')
        gh_create_pages(gh_pat, gh_owner, chosen_repo_name, branch='main', path='/')
    except SystemExit:
        # try gh-pages
        try:
            gh_create_pages(gh_pat, gh_owner, chosen_repo_name, branch='gh-pages', path='/')
        except SystemExit:
            die('Failed to enable GitHub Pages. Ensure the repo contains site content in main or gh-pages branch.')

    # Add custom domain to Pages
    print('Adding custom domain to Pages...')
    gh_create_pages_domain(gh_pat, gh_owner, chosen_repo_name, subdomain)

    # Create Cloudflare DNS CNAME
    target = f'{gh_owner}.github.io'
    print(f'Creating CNAME {subdomain} -> {target} on Cloudflare...')
    cf_create_dns(cf_token, cf_zone_id, subdomain, 'CNAME', target, ttl=120, proxied=False)

    # Wait for DNS
    print('Waiting for DNS propagation...')
    if not dns_cname_resolves_to(target, subdomain, attempts=24, wait=15):
        die('DNS did not propagate within timeout')

    # Wait for GitHub verification
    print('DNS propagated. Waiting for GitHub to verify domain and issue certificate...')
    for i in range(60):
        dom = gh_get_pages_domain(gh_pat, gh_owner, chosen_repo_name, subdomain)
        if dom and dom.get('status') in ('active','verified'):
            print('Domain verified and active')
            break
        time.sleep(30)
    else:
        print('Warning: GitHub did not verify domain within timeout. The site may still become active later.')

    site_url = f'https://{subdomain}'
    repo_url = created_repo.get('html_url')
    msg = f'✅ Subdomain and repository created.\n\nRepository: {repo_url}\nSite: {site_url}\n\nDNS: propagated. If HTTPS is not yet active, allow a few more minutes for the certificate to be issued.'
    print(msg)

    if issue_repo and issue_number:
        post_issue_comment(gh_pat, issue_repo, issue_number, msg)

if __name__=='__main__':
    main()

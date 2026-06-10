#!/usr/bin/env python3
import os
import sys
import time
import argparse
import json
import re
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
            k,v = line.split(':',1)
            data[k.strip().lower()] = v.strip()
    return data

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

def gh_create_repo_from_template(gh_pat, template_owner, template_repo, owner, name, private=False):
    h = {'Authorization': f'token {gh_pat}', 'Accept':'application/vnd.github.baptiste-preview+json'}
    payload = {'owner': owner, 'name': name, 'private': private}
    url = f'{GH_API}/repos/{template_owner}/{template_repo}/generate'
    r = requests.post(url, json=payload, headers=h, timeout=30)
    if r.status_code not in (201,202):
        die(f'Failed to create repo from template: {r.status_code} {r.text}')
    return r.json()

def gh_set_repo_public(gh_pat, owner, repo):
    h = {'Authorization': f'token {gh_pat}', 'Accept':'application/vnd.github+json'}
    url = f'{GH_API}/repos/{owner}/{repo}'
    r = requests.patch(url, json={'private': False}, headers=h, timeout=20)
    if r.status_code>=400:
        die(f'Failed to set repo public: {r.status_code} {r.text}')
    return r.json()

def gh_create_pages(gh_pat, owner, repo, branch='main', path='/'):
    h = {'Authorization': f'token {gh_pat}', 'Accept':'application/vnd.github+json'}
    url = f'{GH_API}/repos/{owner}/{repo}/pages'
    payload = {'source':{'branch': branch, 'path': path}}
    r = requests.put(url, json=payload, headers=h, timeout=30)
    if r.status_code not in (201,200):
        die(f'Failed to create pages site: {r.status_code} {r.text}')
    return r.json()

def gh_create_pages_domain(gh_pat, owner, repo, domain):
    h = {'Authorization': f'token {gh_pat}', 'Accept':'application/vnd.github+json'}
    url = f'{GH_API}/repos/{owner}/{repo}/pages/domains'
    r = requests.post(url, json={'domain': domain}, headers=h, timeout=20)
    if r.status_code not in (201,200):
        die(f'Failed to create pages domain: {r.status_code} {r.text}')
    return r.json()

def gh_get_pages_domain(gh_pat, owner, repo, domain):
    h = {'Authorization': f'token {gh_pat}', 'Accept':'application/vnd.github+json'}
    url = f'{GH_API}/repos/{owner}/{repo}/pages/domains/{domain}'
    r = requests.get(url, headers=h, timeout=20)
    if r.status_code==404:
        return None
    if r.status_code>=400:
        die(f'Failed getting pages domain: {r.status_code} {r.text}')
    return r.json()

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

def post_issue_comment(gh_pat, repo_full, issue_number, body):
    h = {'Authorization': f'token {gh_pat}', 'Accept':'application/vnd.github+json'}
    url = f'{GH_API}/repos/{repo_full}/issues/{issue_number}/comments'
    r = requests.post(url, json={'body': body}, headers=h, timeout=20)
    if r.status_code>=400:
        print(f'Warning: failed posting issue comment: {r.status_code} {r.text}')


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
    template_repo = env.get('TEMPLATE_REPO')
    gh_owner = env.get('GH_OWNER')
    issue_number = env.get('ISSUE_NUMBER')
    issue_repo = env.get('ISSUE_REPO')

    if not all([cf_token, cf_zone_id, cf_zone_name, gh_pat, template_repo, gh_owner]):
        die('Missing required environment variables. Set CF_API_TOKEN, CF_ZONE_ID, CF_ZONE_NAME, GH_PAT, TEMPLATE_REPO, GH_OWNER')

    params = parse_issue_text(args.issue_body)
    subdomain = args.subdomain or params.get('subdomain') or params.get('domain')
    repo_name = args.repo_name or params.get('repo') or params.get('repo_name') or params.get('repository')
    if not subdomain or not repo_name:
        die('Missing subdomain or repo name. Provide in issue body like:\nsubdomain: blog.example.com\nrepo: my-blog')

    if not subdomain.endswith(cf_zone_name):
        die(f'Subdomain {subdomain} is not in zone {cf_zone_name}')
    # Disallow apex/root being used as a 'subdomain'
    if subdomain.rstrip('.') == cf_zone_name.rstrip('.') or subdomain == cf_zone_name:
        die(f'Subdomain {subdomain} is the zone apex; only subdomains are allowed. Provide e.g. blog.{cf_zone_name}')

    print('Verifying Cloudflare zone...')
    zone = cf_get_zone(cf_token, cf_zone_id)
    print('Creating GitHub repo from template...')
    repo = gh_create_repo_from_template(gh_pat, template_owner, template_repo, gh_owner, repo_name, private=False)
    print('Ensuring repo is public...')
    gh_set_repo_public(gh_pat, gh_owner, repo_name)

    # Configure GitHub Pages source (attempt main first)
    try:
        print('Configuring GitHub Pages...')
        gh_create_pages(gh_pat, gh_owner, repo_name, branch='main', path='/')
    except SystemExit:
        # try gh-pages
        try:
            gh_create_pages(gh_pat, gh_owner, repo_name, branch='gh-pages', path='/')
        except SystemExit as e:
            die('Failed to enable GitHub Pages. Ensure the template contains a branch with site content.')

    print('Adding custom domain to Pages...')
    gh_create_pages_domain(gh_pat, gh_owner, repo_name, subdomain)

    # Create Cloudflare DNS CNAME
    target = f'{gh_owner}.github.io'
    print(f'Creating CNAME {subdomain} -> {target} on Cloudflare...')
    cf_create_dns(cf_token, cf_zone_id, subdomain, 'CNAME', target, ttl=120, proxied=False)

    print('Waiting for DNS propagation...')
    if not dns_cname_resolves_to(target, subdomain, attempts=24, wait=15):
        die('DNS did not propagate within timeout')

    print('DNS propagated. Waiting for GitHub to verify domain and issue certificate...')
    for i in range(60):
        dom = gh_get_pages_domain(gh_pat, gh_owner, repo_name, subdomain)
        if dom and dom.get('status') in ('active','verified'):
            print('Domain verified and active')
            break
        time.sleep(30)
    else:
        print('Warning: GitHub did not verify domain within timeout. The site may still become active later.')

    site_url = f'https://{subdomain}'
    repo_url = repo.get('html_url')
    msg = f'✅ Subdomain and repository created.\n\nRepository: {repo_url}\nSite: {site_url}\n\nDNS: propagated. If HTTPS is not yet active, allow a few more minutes for the certificate to be issued.'
    print(msg)

    if issue_repo and issue_number:
        post_issue_comment(gh_pat, issue_repo, issue_number, msg)

if __name__=='__main__':
    main()

"""audit-url: the same page checks against a live site, discovered through its sitemap. Client mode."""
import urllib.error
import uuid
import urllib.request
from urllib.parse import urlsplit

from . import __version__
from . import htmlscan
from . import model as m
from .page_rules import check_page, internal_targets
from .schema_rules import blocked_bots, entity_problem
from .site_rules import sitemap_paths

UA = "seo-audit/%s" % __version__
DEFAULT_PROBE_PRIVATE = ["/README.md", "/.env", "/composer.json", "/package.json"]


class Http:
    def __init__(self, timeout=15):
        self.timeout = timeout
        self.status_cache = {}

    def get(self, url):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                return r.status, r.read().decode(r.headers.get_content_charset() or "utf-8", "replace"), r.geturl()
        except urllib.error.HTTPError as e:
            try:
                body = e.read().decode(e.headers.get_content_charset() or "utf-8", "replace")
            except (OSError, AttributeError):
                body = ""
            return e.code, body, url
        except (urllib.error.URLError, TimeoutError, OSError):
            return None, "", url

    def status(self, url):
        if url not in self.status_cache:
            req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": UA})
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as r:
                    code = r.status
            except urllib.error.HTTPError as e:
                code = e.code
                if code in (403, 405):  # some servers refuse HEAD
                    code = self.get(url)[0]
            except (urllib.error.URLError, TimeoutError, OSError):
                code = None
            self.status_cache[url] = code
        return self.status_cache[url]


def audit_url(base_url, results, config, max_pages=50, max_links=300, http=None):
    http = http or Http()
    parts = urlsplit(base_url)
    origin = "%s://%s" % (parts.scheme, parts.netloc)

    code, robots, _ = http.get(origin + "/robots.txt")
    sitemap_urls = [l.split(":", 1)[1].strip() for l in robots.splitlines() if l.lower().startswith("sitemap:")] if code == 200 else []
    results.check(m.ROBOTS_TXT, "/robots.txt", code == 200 and bool(sitemap_urls),
                  "HTTP %s" % code if code != 200 else "no Sitemap: line")
    if code == 200:
        blocked = blocked_bots(robots)
        results.check(m.AI_SEARCH_CRAWLERS, "/robots.txt", not blocked, "blocks: " + ", ".join(blocked))

    missing = "/seo-audit-missing-page-%s" % uuid.uuid4().hex[:12]
    code404, body404, _ = http.get(origin + missing)
    results.check(m.NOT_FOUND_PAGE, missing, code404 == 404 and "href=" in body404,
                  "a missing page returns HTTP %s (soft 404)" % code404 if code404 != 404 else "404 page has no links")

    code, llms, _ = http.get(origin + "/llms.txt")
    results.check(m.LLMS_TXT, "/llms.txt", code == 200 and bool(llms.strip()), "HTTP %s" % code)

    leaked = [p for p in config.get("probe_private", DEFAULT_PROBE_PRIVATE) if http.status(origin + p) == 200]
    results.check(m.PRIVATE_FILES, "site", not leaked, "reachable: " + ", ".join(leaked))

    # robots.txt may name the sitemap on another host (www vs apex, staging): also try that path on
    # the audited host, then the default location.
    candidates = []
    for u in sitemap_urls + [origin + urlsplit(u).path for u in sitemap_urls] + [origin + "/sitemap.xml"]:
        if u not in candidates:
            candidates.append(u)
    paths, code = None, None
    for sitemap_url in candidates:
        code, xml_text, _ = http.get(sitemap_url)
        # Any host in <loc>: a client's sitemap may say www. while they typed the apex, or the reverse.
        paths = sitemap_paths(xml_text, None) if code == 200 else None
        if paths is not None:
            break
    results.check(m.SITEMAP, urlsplit(sitemap_url).path, paths is not None, "HTTP %s or invalid XML" % code)
    paths = paths or ["/"]
    checked = paths[:max_pages]

    budget = {"links": max_links}

    def link_exists(path):
        url = origin + path
        if url not in http.status_cache:
            if budget["links"] <= 0:
                return None  # unknown: over budget
            budget["links"] -= 1
        code = http.status(url)
        return None if code is None else code < 400

    inlinks, loaded = {}, []
    for path in checked:
        code, html, _ = http.get(origin + path)
        ok = code is not None and code < 400
        results.check(m.SITEMAP_URLS, path, ok, "HTTP %s" % code)
        if not ok:
            continue
        page = htmlscan.scan(html)
        if page.is_redirect():
            continue
        loaded.append(path)
        if path == "/":
            problem = entity_problem(page.jsonld)
            results.check(m.ENTITY_SCHEMA, "/", problem is None, problem or "")
        check_page(results, path, page, origin, link_exists)
        for target in internal_targets(origin + path, page.anchors, origin):
            if target != path:
                inlinks.setdefault(target, set()).add(path)

    if len(checked) == len(paths):  # orphan check only makes sense with every page seen
        for path in loaded:
            if path != "/":
                results.check(m.ORPHAN_PAGES, path, bool(inlinks.get(path)), "no other page links here")
    return len(checked)

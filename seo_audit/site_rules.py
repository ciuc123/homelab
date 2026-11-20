"""audit-site: checks a built static site directory (Jekyll's _site)."""
import fnmatch
import os
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlsplit

from . import htmlscan
from . import model as m
from .page_rules import check_page, internal_targets

SITEMAP_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
DEFAULT_PRIVATE = ["README.md", "AGENT_PROMPTS.md", "*.sh", "tools/*", "tests/*", "workers/*", ".wrangler/*",
                   "Gemfile", "Gemfile.lock", "package.json", ".env", ".env.*"]
DEFAULT_SKIP_PAGES = ["404.html", "google*.html", "assets/*"]


def url_path(rel):
    """'posts/x/index.html' -> '/posts/x/', 'about.html' -> '/about.html'."""
    rel = rel.replace(os.sep, "/")
    if rel == "index.html":
        return "/"
    if rel.endswith("/index.html"):
        return "/" + rel[: -len("index.html")]
    return "/" + rel


class SiteDir:
    def __init__(self, root):
        self.root = os.path.abspath(root)
        self.files = []
        for d, _, fs in os.walk(self.root):
            for f in fs:
                self.files.append(os.path.relpath(os.path.join(d, f), self.root).replace(os.sep, "/"))
        self.fileset = set(self.files)

    def exists(self, path):
        p = path.lstrip("/")
        if p == "" or p.endswith("/"):
            return (p + "index.html") in self.fileset
        return p in self.fileset or (p + "/index.html") in self.fileset or (p + ".html") in self.fileset

    def read(self, rel):
        with open(os.path.join(self.root, rel), encoding="utf-8", errors="replace") as f:
            return f.read()


def _matches(rel, patterns):
    return any(fnmatch.fnmatch(rel, p) for p in patterns)


def audit_site(site_dir, results, config):
    site = SiteDir(site_dir)
    base = config.get("base_url", "https://example.com").rstrip("/")
    origin = "%s://%s" % urlsplit(base)[:2]
    skip = config.get("skip_pages", DEFAULT_SKIP_PAGES)
    pages = [f for f in site.files if f.endswith(".html") and not _matches(f, skip)]

    inlinks = {}
    for rel in sorted(pages):
        path = url_path(rel)
        page = htmlscan.scan(site.read(rel))
        check_page(results, path, page, origin, site.exists)
        for target in internal_targets(origin + path, page.anchors, origin):
            if target != path:
                inlinks.setdefault(target, set()).add(path)

    _site_wide(site, results, config, origin, inlinks)
    return len(pages)


def _site_wide(site, results, config, origin, inlinks):
    robots = site.read("robots.txt") if "robots.txt" in site.fileset else None
    results.check(m.ROBOTS_TXT, "/robots.txt",
                  robots is not None and any(l.lower().startswith("sitemap:") for l in robots.splitlines()),
                  "missing" if robots is None else "no Sitemap: line")

    llms = site.read("llms.txt").strip() if "llms.txt" in site.fileset else ""
    results.check(m.LLMS_TXT, "/llms.txt", bool(llms), "missing or empty")

    private = config.get("private_files", DEFAULT_PRIVATE)
    leaked = sorted(f for f in site.files if _matches(f, private))
    results.check(m.PRIVATE_FILES, "site", not leaked, "published: " + ", ".join(leaked[:10]))

    locs = sitemap_paths(site.read("sitemap.xml"), origin) if "sitemap.xml" in site.fileset else None
    results.check(m.SITEMAP, "/sitemap.xml", locs is not None, "missing or not valid XML")
    for path in locs or []:
        results.check(m.SITEMAP_URLS, path, site.exists(path), "in sitemap but no page")
        if path != "/" and site.exists(path):
            results.check(m.ORPHAN_PAGES, path, bool(inlinks.get(path)), "no other page links here")


def sitemap_paths(xml_text, origin):
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return None
    out = []
    for loc in root.iter(SITEMAP_NS + "loc"):
        parts = urlsplit((loc.text or "").strip())
        if origin is None or not parts.netloc or "%s://%s" % (parts.scheme, parts.netloc) == origin:
            out.append(parts.path or "/")
    return out

"""Per-page rules shared by audit-site (files) and audit-url (HTTP)."""
import json
import re
from urllib.parse import urljoin, urlsplit

from . import model as m

POST_URL = re.compile(r"^/posts/\d{4}-\d{2}-\d{2}-[^/]+/?$")
SKIP_SCHEMES = ("mailto:", "tel:", "javascript:", "data:")


def internal_targets(page_url, hrefs, site_origin):
    """Yield normalized paths of internal links (same origin), without query/fragment."""
    seen = set()
    for href in hrefs:
        href = href.strip()
        if not href or href.startswith("#") or href.lower().startswith(SKIP_SCHEMES):
            continue
        absolute = urljoin(page_url, href)
        parts = urlsplit(absolute)
        if parts.scheme not in ("http", "https") or "%s://%s" % (parts.scheme, parts.netloc) != site_origin:
            continue
        path = parts.path or "/"
        if path.startswith("/cdn-cgi/"):  # Cloudflare-injected (e.g. email obfuscation)
            continue
        if path not in seen:
            seen.add(path)
            yield path


def check_page(results, path, page, site_origin, link_exists):
    """path: URL path of the page ("/posts/x/"). page: htmlscan.PageScan. link_exists(path) -> bool or None (unknown)."""
    t = path
    titles = [x for x in page.titles if x]
    results.check(m.SINGLE_TITLE, t, len(page.titles) == 1 and len(titles) == 1, "%d <title> elements" % len(page.titles))

    desc = (page.meta(name="description") or "").strip()
    results.check(m.META_DESCRIPTION, t, bool(desc), "no meta description")
    if desc:
        results.check(m.META_DESCRIPTION_LENGTH, t, 50 <= len(desc) <= 160, "meta description is %d chars" % len(desc))

    canonical = page.canonical() or ""
    results.check(m.CANONICAL, t, canonical.startswith(("http://", "https://")), "canonical is %r" % (canonical or None))

    results.check(m.SINGLE_H1, t, page.h1_count == 1, "%d <h1> elements" % page.h1_count)

    bad = []
    for raw in page.jsonld:
        try:
            json.loads(raw)
        except ValueError as e:
            bad.append(str(e))
    results.check(m.JSON_LD_PRESENT, t, bool(page.jsonld), "no JSON-LD")
    if page.jsonld:
        results.check(m.JSON_LD_VALID, t, not bad, "; ".join(bad))

    results.check(m.OG_IMAGE, t, bool((page.meta(prop="og:image") or "").strip()), "no og:image")

    if page.imgs:
        missing = [i.get("src", "?") for i in page.imgs if "alt" not in i]
        results.check(m.IMG_ALT, t, not missing, "no alt on: " + ", ".join(missing[:5]))

    if page.forms:
        empty = [f.get("id") or "(no id)" for f in page.forms if f.get("action", "").strip() in ("", "#")]
        results.check(m.FORM_ACTION, t, not empty, "form without action: " + ", ".join(empty))

    if POST_URL.match(path):
        results.check(m.POST_CTA, t, "post-cta" in page.classes, "no .post-cta block")

    broken = []
    for target in internal_targets(site_origin + path, page.anchors, site_origin):
        ok = link_exists(target)
        if ok is False:
            broken.append(target)
    results.check(m.INTERNAL_LINKS, t, not broken, "broken: " + ", ".join(broken[:10]))

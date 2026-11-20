import functools
import http.server
import os
import threading
import unittest

from _helpers import failed, fixture
from seo_audit import model as m
from seo_audit.url_audit import audit_url


class _Quiet(http.server.SimpleHTTPRequestHandler):
    """Static server that, like real hosts, serves the site's 404.html with status 404 when there is one."""

    def log_message(self, *args):
        pass

    def send_error(self, code, message=None, explain=None):
        page = os.path.join(self.directory, "404.html")
        if code == 404 and os.path.exists(page):
            with open(page, "rb") as f:
                body = f.read()
            self.send_response(404)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)
            return
        super().send_error(code, message, explain)


def serve(directory):
    handler = functools.partial(_Quiet, directory=directory)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, "http://127.0.0.1:%d" % server.server_address[1]


class UrlAuditTest(unittest.TestCase):
    def audit(self, name):
        server, base = serve(fixture(name))
        try:
            r = m.Results()
            pages = audit_url(base + "/", r, {})
            return r, pages
        finally:
            server.shutdown()
            server.server_close()

    def test_good_site_over_http(self):
        r, pages = self.audit("site_good")
        self.assertEqual(pages, 4)
        # The fixture's robots.txt points at example.com, which isn't reachable from the test,
        # but robots-txt only checks that a Sitemap line exists. Canonicals are absolute.
        self.assertEqual(failed(r), {})

    def test_bad_site_over_http(self):
        r, _ = self.audit("site_bad")
        f = failed(r)
        self.assertEqual(f[m.ROBOTS_TXT], {"/robots.txt"})
        self.assertEqual(f[m.LLMS_TXT], {"/llms.txt"})
        self.assertEqual(f[m.PRIVATE_FILES], {"site"})
        self.assertEqual(f[m.SITEMAP_URLS], {"/gone/"})
        self.assertEqual(f[m.POST_CTA], {"/posts/2026-01-10-bad-post/"})
        self.assertEqual(f[m.FORM_ACTION], {"/contact/"})
        self.assertIn("/", f[m.INTERNAL_LINKS])
        self.assertEqual(f[m.ORPHAN_PAGES], {"/orphan/"})
        self.assertEqual(f[m.ENTITY_SCHEMA], {"/"})
        self.assertEqual(len(f[m.NOT_FOUND_PAGE]), 1)  # default error page has no links

    def test_soft_404_is_reported(self):
        class Always200:
            status_cache = {}

            def get(self, url):
                if url.endswith("/robots.txt"):
                    return 200, "User-agent: *\nAllow: /\nSitemap: https://x.example/sitemap.xml\n", url
                if url.endswith("/sitemap.xml"):
                    return 200, '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://x.example/</loc></url></urlset>', url
                return 200, '<html><head><title>T</title></head><body><h1>Home</h1><a href="/">x</a></body></html>', url

            def status(self, url):
                return 404
        r = m.Results()
        audit_url("https://x.example/", r, {}, http=Always200())
        msgs = [c[3] for c in r.checks if c[0] == m.NOT_FOUND_PAGE]
        self.assertEqual(len(msgs), 1)
        self.assertIn("soft 404", msgs[0])


if __name__ == "__main__":
    unittest.main()

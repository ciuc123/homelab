import functools
import http.server
import threading
import unittest

from _helpers import failed, fixture
from seo_audit import model as m
from seo_audit.url_audit import audit_url


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


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


if __name__ == "__main__":
    unittest.main()

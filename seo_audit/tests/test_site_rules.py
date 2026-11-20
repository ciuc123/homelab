import unittest

from _helpers import failed, fixture
from seo_audit import htmlscan
from seo_audit import model as m
from seo_audit.page_rules import internal_targets
from seo_audit.site_rules import audit_site, url_path

CONFIG = {"base_url": "https://example.com"}


class SiteRulesTest(unittest.TestCase):
    def test_good_site_passes_everything(self):
        r = m.Results()
        self.assertEqual(audit_site(fixture("site_good"), r, CONFIG), 4)
        self.assertEqual(failed(r), {})
        evaluated = {c[0] for c in r.checks}
        for rule in (m.POST_CTA, m.FORM_ACTION, m.IMG_ALT, m.ORPHAN_PAGES, m.LLMS_TXT, m.ROBOTS_TXT):
            self.assertIn(rule, evaluated)

    def test_bad_site_fails_every_site_rule(self):
        r = m.Results()
        audit_site(fixture("site_bad"), r, CONFIG)
        f = failed(r)
        self.assertEqual(f[m.SINGLE_TITLE], {"/"})
        self.assertEqual(f[m.META_DESCRIPTION], {"/"})
        self.assertEqual(f[m.META_DESCRIPTION_LENGTH], {"/contact/"})
        self.assertEqual(f[m.CANONICAL], {"/"})
        self.assertEqual(f[m.SINGLE_H1], {"/"})
        self.assertEqual(f[m.JSON_LD_VALID], {"/"})
        self.assertEqual(f[m.JSON_LD_PRESENT], {"/posts/2026-01-10-bad-post/"})
        self.assertEqual(f[m.OG_IMAGE], {"/"})
        self.assertEqual(f[m.IMG_ALT], {"/"})
        self.assertEqual(f[m.FORM_ACTION], {"/contact/"})
        self.assertEqual(f[m.POST_CTA], {"/posts/2026-01-10-bad-post/"})
        self.assertIn("/", f[m.INTERNAL_LINKS])
        self.assertEqual(f[m.ROBOTS_TXT], {"/robots.txt"})
        self.assertEqual(f[m.LLMS_TXT], {"/llms.txt"})
        self.assertEqual(f[m.PRIVATE_FILES], {"site"})
        self.assertEqual(f[m.SITEMAP_URLS], {"/gone/"})
        self.assertEqual(f[m.ORPHAN_PAGES], {"/orphan/"})

    def test_broken_link_message_names_the_target(self):
        r = m.Results()
        audit_site(fixture("site_bad"), r, CONFIG)
        msgs = [c[3] for c in r.checks if c[0] == m.INTERNAL_LINKS and not c[2]]
        self.assertTrue(any("/missing/" in x for x in msgs))

    def test_private_files_lists_what_leaked(self):
        r = m.Results()
        audit_site(fixture("site_bad"), r, CONFIG)
        msg = [c[3] for c in r.checks if c[0] == m.PRIVATE_FILES][0]
        self.assertIn("README.md", msg)
        self.assertIn("deploy.sh", msg)

    def test_url_path(self):
        self.assertEqual(url_path("index.html"), "/")
        self.assertEqual(url_path("posts/x/index.html"), "/posts/x/")
        self.assertEqual(url_path("about.html"), "/about.html")

    def test_internal_targets_filters_and_resolves(self):
        hrefs = ["/a/", "b/", "#top", "mailto:x@y.z", "https://other.example/", "https://example.com/c/?q=1#f",
                 "/cdn-cgi/l/email-protection", "javascript:void(0)", "/a/"]
        self.assertEqual(list(internal_targets("https://example.com/posts/x/", hrefs, "https://example.com")),
                         ["/a/", "/posts/x/b/", "/c/"])

    def test_title_inside_svg_body_is_ignored(self):
        page = htmlscan.scan("<html><head><title>T</title></head><body><svg><title>icon</title></svg></body></html>")
        self.assertEqual(page.titles, ["T"])


if __name__ == "__main__":
    unittest.main()

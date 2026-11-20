import contextlib
import io
import json
import os
import tempfile
import unittest

from _helpers import fixture
from seo_audit import model as m
from seo_audit import report
from seo_audit.cli import main
from seo_audit.guidance import GUIDANCE, fix_order
from seo_audit.site_rules import audit_site

CONFIG = {"base_url": "https://example.com"}


def bad_results():
    r = m.Results()
    audit_site(fixture("site_bad"), r, CONFIG)
    return r


class GuidanceTest(unittest.TestCase):
    def test_every_rule_has_guidance(self):
        self.assertEqual(set(GUIDANCE), set(m.RULES))
        for rule_id, (impact, why, how) in GUIDANCE.items():
            self.assertIn(impact, (1, 2, 3), rule_id)
            self.assertTrue(why and how, rule_id)

    def test_fix_order_is_impact_then_count(self):
        by_rule = {
            "tags-present": {"failed": 9}, "og-image": {"failed": 2}, "internal-links": {"failed": 1},
            "title-length": {"failed": 5}, "canonical": {"failed": 0},
        }
        self.assertEqual(fix_order(by_rule), ["internal-links", "title-length", "og-image", "tags-present"])


class ReportTest(unittest.TestCase):
    def test_markdown_has_fix_first_and_escapes_html(self):
        text = report.to_markdown(bad_results(), {"mode": "audit-site", "target": "x", "title": "Acme"})
        self.assertIn("# SEO audit report: Acme", text)
        self.assertIn("## What to fix first", text)
        self.assertIn("`<form>`", text)
        self.assertIn("(2 `<h1>` elements)", text)
        self.assertNotIn(" <form>", text.replace("`<form>`", ""))

    def test_summary_is_short_and_ranked(self):
        text = report.to_summary(bad_results(), {"target": "https://example.com"}, report_url="https://r/1.md")
        self.assertIn("top 5 of", text)
        self.assertEqual(sum(1 for l in text.splitlines() if l[:2] in ("1.", "2.", "3.", "4.", "5.", "6.")), 5)
        self.assertTrue(text.rstrip().endswith("Full report: https://r/1.md"))
        self.assertIn("(broken: /missing/)", text)

    def test_summary_when_everything_passes(self):
        r = m.Results()
        audit_site(fixture("site_good"), r, CONFIG)
        self.assertIn("Every check passed.", report.to_summary(r, {"target": "x"}))

    def test_previous_report_shows_changes(self):
        previous = {"meta": {"date": "2026-01-01"}, "summary": {"score": 50}, "rules": {"internal-links": {"failed": 7}}}
        text = report.to_summary(bad_results(), {"target": "x"}, previous)
        self.assertIn("Since 2026-01-01: score 50 → 61 (+11)", text)
        self.assertIn("3 failing (was 7)", text)


class CliReportOptionsTest(unittest.TestCase):
    def test_title_previous_and_summary(self):
        tmp = tempfile.mkdtemp()
        cfg, prev, summ = (os.path.join(tmp, n) for n in ("c.json", "p.json", "s.md"))
        with open(cfg, "w") as f:
            json.dump(CONFIG, f)
        with open(prev, "w") as f:
            json.dump({"meta": {"date": "2026-01-01"}, "summary": {"score": 40}, "rules": {}}, f)
        with contextlib.redirect_stdout(io.StringIO()):
            code = main(["audit-site", fixture("site_bad"), "--config", cfg, "--quiet", "--title", "Acme",
                         "--previous", prev, "--summary", summ, "--report-url", "https://r/x.md"])
        self.assertEqual(code, 1)
        with open(summ) as f:
            text = f.read()
        self.assertIn("## SEO audit: Acme", text)
        self.assertIn("score 40 → 61", text)

    def test_unreadable_previous_is_ignored(self):
        tmp = tempfile.mkdtemp()
        summ = os.path.join(tmp, "s.md")
        err = io.StringIO()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
            main(["audit-site", fixture("site_good"), "--base-url", "https://example.com", "--quiet",
                  "--previous", os.path.join(tmp, "missing.json"), "--summary", summ])
        self.assertIn("previous report ignored", err.getvalue())
        self.assertTrue(os.path.exists(summ))


if __name__ == "__main__":
    unittest.main()

import contextlib
import io
import json
import os
import tempfile
import unittest

from _helpers import fixture
from seo_audit.cli import main


def run(*argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        code = main(list(argv))
    return code, out.getvalue()


class CliTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.config = os.path.join(self.tmp, "c.json")

    def write_config(self, data):
        with open(self.config, "w") as f:
            json.dump(data, f)

    def test_good_site_exits_zero_and_writes_reports(self):
        self.write_config({"base_url": "https://example.com", "min_words": 20})
        js, md = os.path.join(self.tmp, "r.json"), os.path.join(self.tmp, "r.md")
        code, out = run("audit-site", fixture("site_good"), "--posts", fixture("posts_good"), "--config", self.config,
                        "--today", "2026-11-20", "--json", js, "--markdown", md)
        self.assertEqual(code, 0, out)
        self.assertIn("Score 100/100", out)
        with open(js) as f:
            self.assertEqual(json.load(f)["summary"]["errors"], 0)
        with open(md) as f:
            self.assertIn("**Score: 100/100**", f.read())

    def test_errors_exit_one(self):
        self.write_config({"base_url": "https://example.com"})
        code, out = run("audit-site", fixture("site_bad"), "--config", self.config, "--quiet")
        self.assertEqual(code, 1)

    def test_severity_override_turns_errors_into_warnings(self):
        from seo_audit import model as m
        self.write_config({"base_url": "https://example.com", "severity": {r: "warning" for r in m.RULES}})
        js = os.path.join(self.tmp, "r.json")
        code, _ = run("audit-site", fixture("site_bad"), "--config", self.config, "--quiet", "--json", js)
        self.assertEqual(code, 0)
        with open(js) as f:
            s = json.load(f)["summary"]
        self.assertEqual(s["errors"], 0)
        self.assertGreater(s["warnings"], 0)

    def test_off_removes_rule_from_score(self):
        self.write_config({"severity": {"og-image": "off"}, "base_url": "https://example.com"})
        js = os.path.join(self.tmp, "r.json")
        run("audit-site", fixture("site_bad"), "--config", self.config, "--quiet", "--json", js)
        with open(js) as f:
            self.assertNotIn("og-image", json.load(f)["rules"])

    def test_missing_or_invalid_config_is_a_clean_error(self):
        code, out = run("lint-content", fixture("posts_good"), "--config", os.path.join(self.tmp, "nope.json"))
        self.assertEqual(code, 2)
        self.assertIn("config error", out)
        with open(self.config, "w") as f:
            f.write("{not json")
        code, out = run("lint-content", fixture("posts_good"), "--config", self.config)
        self.assertEqual(code, 2)

    def test_unknown_rule_in_config_is_rejected(self):
        self.write_config({"severity": {"no-such-rule": "warning"}})
        code, out = run("lint-content", fixture("posts_good"), "--config", self.config)
        self.assertEqual(code, 2)
        self.assertIn("no-such-rule", out)


if __name__ == "__main__":
    unittest.main()

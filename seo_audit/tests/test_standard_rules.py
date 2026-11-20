import unittest

from _helpers import failed, fixture
from seo_audit import model as m
from seo_audit.content_rules import lint_content
from seo_audit.schema_rules import faq_problems

import datetime as dt

CONFIG = {"min_words": 20, "standard_since": "2026-11-21"}
LATER = dt.date(2026, 11, 30)


class PostStandardTest(unittest.TestCase):
    def lint(self, config=CONFIG):
        r = m.Results()
        lint_content(fixture("posts_standard"), r, config, LATER)
        return r

    def test_good_standard_post_passes(self):
        f = failed(self.lint())
        for rule, targets in f.items():
            self.assertNotIn("_posts/2026-11-21-good-standard.md", targets, rule)

    def test_bad_standard_post_fails_each_rule(self):
        f = failed(self.lint())
        bad = "_posts/2026-11-22-bad-standard.md"
        for rule in (m.POST_TLDR, m.FAQ_ENTRIES, m.QUESTION_HEADING, m.SOURCES_SECTION, m.LAST_MODIFIED):
            self.assertIn(bad, f.get(rule, set()), rule)

    def test_posts_before_the_cutoff_are_exempt(self):
        r = self.lint()
        old = "_posts/2026-11-01-before-standard.md"
        evaluated = {c[0] for c in r.checks if c[1] == old}
        self.assertFalse(evaluated & {m.POST_TLDR, m.QUESTION_HEADING, m.SOURCES_SECTION})

    def test_no_cutoff_means_no_standard_rules(self):
        r = self.lint({"min_words": 20})
        self.assertFalse({c[0] for c in r.checks} & {m.POST_TLDR, m.QUESTION_HEADING, m.SOURCES_SECTION, m.FAQ_ENTRIES})


class FaqSchemaTest(unittest.TestCase):
    def test_valid_faq(self):
        ok = '{"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": "Q?", "acceptedAnswer": {"@type": "Answer", "text": "A."}}]}'
        self.assertEqual(faq_problems([ok]), (1, []))

    def test_invalid_faq(self):
        self.assertEqual(faq_problems(['{"@type": "FAQPage"}'])[1], ["FAQPage without questions"])
        n, problems = faq_problems(['{"@graph": [{"@type": "FAQPage", "mainEntity": {"@type": "Question", "name": "Q?"}}]}'])
        self.assertEqual((n, len(problems)), (1, 1))

    def test_no_faq(self):
        self.assertEqual(faq_problems(['{"@type": "WebPage"}']), (0, []))


if __name__ == "__main__":
    unittest.main()

import unittest

from _helpers import TODAY, failed, fixture
from seo_audit import model as m
from seo_audit.content_rules import lint_content, word_count

CONFIG = {"min_words": 20}


class ContentRulesTest(unittest.TestCase):
    def test_good_posts_pass_everything(self):
        r = m.Results()
        self.assertEqual(lint_content(fixture("posts_good"), r, CONFIG, TODAY), 2)
        self.assertEqual(failed(r), {})
        self.assertIn(m.DESCRIPTION_LENGTH, {c[0] for c in r.checks})

    def test_bad_posts_fail_the_right_rules(self):
        r = m.Results()
        lint_content(fixture("posts_bad"), r, CONFIG, TODAY)
        f = failed(r)
        mismatch = "_posts/2025-01-01-mismatch.md"
        for rule in (m.TITLE_LENGTH, m.DESCRIPTION_LENGTH, m.TAGS_PRESENT, m.DATE_MATCHES_FILENAME, m.STALE_YEAR, m.MIN_WORDS):
            self.assertIn(mismatch, f.get(rule, set()), rule)
        self.assertEqual(f[m.NO_FUTURE_DATE], {"_posts/2099-01-01-future.md"})
        self.assertIn("_posts/2099-01-01-future.md", f[m.DESCRIPTION_PRESENT])
        self.assertEqual(f[m.FRONT_MATTER], {"_posts/2025-02-02-no-front-matter.md", "_posts/2025-03-03-unclosed.md"})

    def test_version_numbers_are_not_stale_years(self):
        r = m.Results()
        lint_content(fixture("posts_good"), r, CONFIG, TODAY)
        self.assertNotIn(m.STALE_YEAR, failed(r))

    def test_word_count_skips_code_and_tags(self):
        self.assertEqual(word_count("one two\n```php\nthree four five\n```\n<b>six</b> {% raw %}"), 3)


if __name__ == "__main__":
    unittest.main()

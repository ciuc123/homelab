import unittest

from _helpers import fixture  # noqa: F401  (sets sys.path)
from seo_audit import frontmatter as fm


class FrontMatterTest(unittest.TestCase):
    def test_scalars_lists_and_quotes(self):
        d = fm.parse('title: "Say \\"hi\\""\nother: \'it\'\'s\'\nn: 3\nflag: true\ntags: [a, "b, c", d]\nbare: text # comment\n')
        self.assertEqual(d["title"], 'Say "hi"')
        self.assertEqual(d["other"], "it's")
        self.assertEqual(d["n"], 3)
        self.assertIs(d["flag"], True)
        self.assertEqual(d["tags"], ["a", "b, c", "d"])
        self.assertEqual(d["bare"], "text")

    def test_block_list_and_folded_scalar(self):
        d = fm.parse("tags:\n  - one\n  - two\ndesc: >-\n  first line\n  second line\nafter: x\n")
        self.assertEqual(d["tags"], ["one", "two"])
        self.assertEqual(d["desc"], "first line second line")
        self.assertEqual(d["after"], "x")

    def test_literal_scalar_keeps_lines(self):
        self.assertEqual(fm.parse("body: |\n  a\n  b\n")["body"], "a\nb")

    def test_empty_inline_list(self):
        self.assertEqual(fm.parse("tags: []\n")["tags"], [])

    def test_split_requires_front_matter(self):
        with self.assertRaises(fm.FrontMatterError):
            fm.split("no front matter")
        with self.assertRaises(fm.FrontMatterError):
            fm.split("---\ntitle: x\n")
        meta, body = fm.split("---\ntitle: x\n---\nbody\n")
        self.assertEqual((meta, body), ("title: x\n", "body\n"))

    def test_unparseable_line(self):
        with self.assertRaises(fm.FrontMatterError):
            fm.parse("this is not yaml\n")


if __name__ == "__main__":
    unittest.main()

import unittest

from _helpers import fixture  # noqa: F401  (sets sys.path)
from seo_audit.schema_rules import articles_without_author, blocked_bots, entity_problem, nodes


class JsonLdTest(unittest.TestCase):
    def test_nodes_flattens_graph_and_lists_and_skips_invalid(self):
        blocks = ['{"@graph": [{"@type": "Person"}, {"@type": "WebSite"}]}', '[{"@type": "Thing"}]', '{bad']
        self.assertEqual([n.get("@type") for n in nodes(blocks)], [None, "Person", "WebSite", "Thing"])

    def test_entity_needs_name_and_same_as(self):
        self.assertIsNone(entity_problem(['{"@type": ["Organization"], "name": "Acme", "sameAs": "https://x.example"}']))
        self.assertIsNone(entity_problem(['{"@type": "Dentist", "name": "Smile", "sameAs": ["https://g.example"]}']))
        self.assertIn("no Person", entity_problem(['{"@type": "WebSite", "name": "x"}']))
        self.assertIn("sameAs", entity_problem(['{"@type": "Person", "name": "Ann"}']))

    def test_article_author(self):
        self.assertEqual(articles_without_author(['{"@type": "BlogPosting", "author": {"@id": "#p"}}']), (1, 0))
        self.assertEqual(articles_without_author(['{"@type": "Article", "author": "Ann"}']), (1, 0))
        self.assertEqual(articles_without_author(['{"@type": "NewsArticle", "author": [{"name": "A"}]}']), (1, 0))
        self.assertEqual(articles_without_author(['{"@type": "Article"}', '{"@type": "Article", "author": {}}']), (2, 2))
        self.assertEqual(articles_without_author(['{"@type": "WebPage"}']), (0, 0))


class RobotsTest(unittest.TestCase):
    def test_disallow_all_blocks_everyone(self):
        self.assertIn("Googlebot", blocked_bots("User-agent: *\nDisallow: /\n"))

    def test_specific_group_overrides_star(self):
        txt = "User-agent: *\nDisallow: /\n\nUser-agent: Googlebot\nUser-agent: Bingbot\nAllow: /\n"
        b = blocked_bots(txt)
        self.assertNotIn("Googlebot", b)
        self.assertNotIn("Bingbot", b)
        self.assertIn("PerplexityBot", b)

    def test_blocking_training_bots_only_is_fine(self):
        txt = "User-agent: GPTBot\nDisallow: /\nUser-agent: ClaudeBot\nDisallow: /\n\nUser-agent: *\nAllow: /\n"
        self.assertEqual(blocked_bots(txt), [])

    def test_partial_disallow_and_comments_are_fine(self):
        self.assertEqual(blocked_bots("User-agent: * # all\nDisallow: /admin/\nDisallow:\n"), [])

    def test_case_insensitive_agents(self):
        self.assertIn("PerplexityBot", blocked_bots("user-agent: perplexitybot\ndisallow: /\n"))


if __name__ == "__main__":
    unittest.main()

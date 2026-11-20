import contextlib
import io
import unittest
from unittest import mock

from scripts import issue_to_audit as ita

PUBLIC = lambda host: ["93.184.216.34"]  # noqa: E731

BODY = """### Target site

https://Shop.Example.com/some/page?x=1

### Max pages

500

### Client name

Acme <script>alert(1)</script> & Co

### Notes

_No response_
"""


class ParseTest(unittest.TestCase):
    def test_issue_form(self):
        req = ita.parse(BODY)
        out = ita.build(req["url"], req["max_pages"], req["client"], resolve=PUBLIC)
        self.assertEqual(out, {
            "url": "https://shop.example.com", "host": "shop.example.com", "max_pages": "200",
            "client": "Acme scriptalert(1)script & Co", "slug": "shop-example-com",
        })

    def test_defaults(self):
        out = ita.build("ciuculescu.com", "", "", resolve=PUBLIC)
        self.assertEqual((out["url"], out["max_pages"], out["client"]), ("https://ciuculescu.com", "50", ""))

    def test_no_response_target_is_an_error(self):
        with self.assertRaises(ita.RequestError):
            ita.build(ita.parse("### Target site\n\n_No response_\n")["url"], "", "", resolve=PUBLIC)


class ValidateUrlTest(unittest.TestCase):
    def rejects(self, url, resolve=PUBLIC):
        with self.assertRaises(ita.RequestError, msg=url):
            ita.validate_url(url, resolve)

    def test_rejects_non_public_targets(self):
        for url in ("ftp://example.org", "http://127.0.0.1/", "http://[::1]/", "http://10.0.0.5", "http://localhost/",
                    "http://router.lan", "http://nas.local", "https://user:pw@example.org", "https://example.org:8080",
                    "https://exa mple.org", "javascript:alert(1)", "https://intranet", "https://x.internal"):
            self.rejects(url)

    def test_ip_literal_gets_a_clear_message(self):
        for url in ("http://192.168.0.1", "http://[2001:db8::1]/"):
            with self.assertRaisesRegex(ita.RequestError, "not an IP address"):
                ita.validate_url(url, PUBLIC)

    def test_rejects_names_that_resolve_privately(self):
        self.rejects("https://sneaky.example.org", resolve=lambda h: ["192.168.1.10"])
        self.rejects("https://sneaky.example.org", resolve=lambda h: ["93.184.216.34", "127.0.0.1"])
        self.rejects("https://sneaky.example.org", resolve=lambda h: ["fd00::1"])

    def test_rejects_unresolvable(self):
        def fail(host):
            raise OSError("no such host")
        self.rejects("https://does-not-exist.example.org", resolve=fail)

    def test_accepts_standard_ports_and_trailing_dot(self):
        self.assertEqual(ita.validate_url("http://Example.org:80/", PUBLIC), ("http://example.org", "example.org"))
        self.assertEqual(ita.validate_url("https://example.org.:443", PUBLIC), ("https://example.org", "example.org"))


class MainTest(unittest.TestCase):
    def run_main(self, argv, stdin=""):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(ita, "_resolve", PUBLIC), mock.patch("sys.stdin", io.StringIO(stdin)), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = ita.main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_issue_body_from_stdin(self):
        code, out, _ = self.run_main([], BODY)
        self.assertEqual(code, 0)
        self.assertIn("url=https://shop.example.com\n", out)
        self.assertIn("max_pages=200\n", out)

    def test_manual_run_arguments(self):
        code, out, _ = self.run_main(["--url", "https://example.org", "--max-pages", "10", "--client", "Me"])
        self.assertEqual(code, 0)
        self.assertIn("client=Me\n", out)

    def test_invalid_request_exits_2_with_message(self):
        code, out, err = self.run_main(["--url", "http://localhost"])
        self.assertEqual((code, out), (2, ""))
        self.assertIn("public domain", err)


if __name__ == "__main__":
    unittest.main()

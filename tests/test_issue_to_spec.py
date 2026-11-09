import unittest

from scripts.issue_to_spec import parse, sections

BODY = """### Client name

acme-shop

### Domain

Shop.Example.com

### Site name

_No response_

### Frontend template

ciuc123/frontend-base

### Site options (site.config toggles)

- [x] Owner dashboard (admin) enabled
- [ ] Visitor accounts (sign-in) enabled

### Owner email

me@example.com

### Run options

- [x] Dry run (print the plan, create nothing)
- [ ] Turn the Cloudflare proxy on after the domain is verified
- [ ] Dev version (also provision dev.<domain>, served from the development branch)
"""


class ParseTest(unittest.TestCase):
    def test_form_becomes_a_spec(self):
        spec, dry = parse(BODY)
        self.assertEqual(spec["name"], "acme-shop")
        self.assertEqual(spec["domain"], "shop.example.com")
        self.assertNotIn("site_name", spec)  # "No response" keeps the default
        self.assertIs(spec["admin_enabled"], True)
        self.assertIs(spec["accounts_enabled"], False)
        self.assertIs(spec["proxy_after_verify"], False)
        self.assertIs(spec["dev_enabled"], False)
        self.assertTrue(dry)

    def test_real_run_when_dry_run_is_not_ticked(self):
        self.assertFalse(parse(BODY.replace("- [x] Dry run", "- [ ] Dry run"))[1])

    def test_dev_version_ticked_reaches_the_spec(self):
        spec, _ = parse(BODY.replace("- [ ] Dev version", "- [x] Dev version"))
        self.assertIs(spec["dev_enabled"], True)

    def test_missing_toggle_section_keeps_defaults_on(self):
        spec, _ = parse("### Client name\n\nx1\n\n### Domain\n\nx1.example.com\n")
        self.assertTrue(spec["admin_enabled"] and spec["accounts_enabled"])

    def test_windows_line_endings_and_garbage_do_not_crash(self):
        self.assertEqual(sections(BODY.replace("\n", "\r\n"))["Client name"], "acme-shop")
        self.assertEqual(parse("")[0], {"admin_enabled": True, "accounts_enabled": True, "template": "ciuc123/frontend-base", "proxy_after_verify": False, "dev_enabled": False})

    def test_shell_metacharacters_stay_data(self):
        spec, _ = parse("### Client name\n\n$(rm -rf /); `id`\n\n### Domain\n\na.example.com\n")
        self.assertEqual(spec["name"], "$(rm -rf /); `id`")  # infra-template's validation rejects it, nothing runs it


if __name__ == "__main__":
    unittest.main()

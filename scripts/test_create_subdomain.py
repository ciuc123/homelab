import unittest
import sys
import types

# The unit under test does not use DNS, so keep this focused test runnable before
# the workflow dependencies have been installed.
if 'dns' not in sys.modules:
    dns = types.ModuleType('dns')
    dns.resolver = types.ModuleType('dns.resolver')
    sys.modules['dns'] = dns
    sys.modules['dns.resolver'] = dns.resolver

from scripts.create_subdomain import resolve_template_reference, split_template_reference


class SplitTemplateReferenceTests(unittest.TestCase):
    def test_bare_name_uses_default_owner(self):
        self.assertEqual(
            split_template_reference('template-barber', 'ciuc123'),
            ('ciuc123', 'template-barber'),
        )

    def test_full_name_overrides_default_owner(self):
        self.assertEqual(
            split_template_reference('other/template-barber', 'ciuc123'),
            ('other', 'template-barber'),
        )

    def test_issue_template_overrides_configured_default(self):
        self.assertEqual(
            resolve_template_reference('template-barber', 'some-other-template', 'ciuc123'),
            ('ciuc123', 'template-barber'),
        )


if __name__ == '__main__':
    unittest.main()

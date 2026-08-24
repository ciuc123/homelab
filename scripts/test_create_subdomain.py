import unittest
import sys
import types
from unittest.mock import patch

# The unit under test does not use DNS, so keep this focused test runnable before
# the workflow dependencies have been installed.
if 'dns' not in sys.modules:
    dns = types.ModuleType('dns')
    dns.resolver = types.ModuleType('dns.resolver')
    sys.modules['dns'] = dns
    sys.modules['dns.resolver'] = dns.resolver

from scripts.create_subdomain import (
    gh_wait_for_default_branch,
    resolve_template_reference,
    split_template_reference,
)


class FakeResponse:
    def __init__(self, status_code, payload=None, text=''):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self):
        return self._payload


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

    @patch('scripts.create_subdomain.time.sleep')
    @patch('scripts.create_subdomain.gh_request')
    def test_waits_for_template_default_branch_ref(self, request, _sleep):
        request.side_effect = [
            FakeResponse(200, {'default_branch': 'main'}),
            FakeResponse(409, text='Git Repository is empty'),
            FakeResponse(200, {'default_branch': 'main'}),
            FakeResponse(200),
        ]

        self.assertEqual(
            gh_wait_for_default_branch('token', 'ciuc123', 'template-barber', attempts=2, wait=0),
            'main',
        )


if __name__ == '__main__':
    unittest.main()

import datetime as dt
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

FIXTURES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")
TODAY = dt.date(2026, 11, 20)


def fixture(*parts):
    return os.path.join(FIXTURES, *parts)


def failed(results):
    """{rule_id: set(targets)} for every failing check."""
    out = {}
    for rule_id, target, passed, _ in results.checks:
        if not passed:
            out.setdefault(rule_id, set()).add(target)
    return out

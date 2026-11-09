#!/usr/bin/env python3
"""Turns the body of a "New client site" issue form into the client.json that infra-template reads.

An issue form renders as `### Label` sections; checkboxes as `- [x] text` / `- [ ] text`. The body is untrusted text (it comes
from an issue), so it is only parsed here, never executed or interpolated into a shell; infra-template validates every field."""

from __future__ import annotations

import json
import sys

NO_RESPONSE = "_No response_"


def sections(body: str) -> dict[str, str]:
    out: dict[str, str] = {}
    label = None
    lines: list[str] = []
    for line in (body or "").replace("\r\n", "\n").split("\n"):
        if line.startswith("### "):
            if label is not None:
                out[label] = "\n".join(lines).strip()
            label, lines = line[4:].strip(), []
        elif label is not None:
            lines.append(line)
    if label is not None:
        out[label] = "\n".join(lines).strip()
    return {k: ("" if v == NO_RESPONSE else v) for k, v in out.items()}


def ticked(section: str, text: str) -> bool:
    for line in section.splitlines():
        line = line.strip()
        if line.lower().startswith("- [x]") and text.lower() in line.lower():
            return True
    return False


def parse(body: str) -> tuple[dict, bool]:
    """Returns (spec dict, dry_run). A missing toggle section means "keep the default" (on)."""
    s = sections(body)
    toggles = s.get("Site options (site.config toggles)", "")
    options = s.get("Run options", "")
    spec = {
        "name": s.get("Client name", ""),
        "domain": s.get("Domain", "").lower(),
        "site_name": s.get("Site name", ""),
        "template": s.get("Frontend template", "") or "ciuc123/frontend-base",
        "owner_email": s.get("Owner email", ""),
        "admin_emails": s.get("Owner email", ""),
        "admin_enabled": ticked(toggles, "Owner dashboard") if toggles else True,
        "accounts_enabled": ticked(toggles, "Visitor accounts") if toggles else True,
        "proxy_after_verify": ticked(options, "Cloudflare proxy"),
    }
    return {k: v for k, v in spec.items() if v != ""}, ticked(options, "Dry run")


def main() -> int:
    body = sys.stdin.read()
    spec, dry_run = parse(body)
    if not spec.get("name") or not spec.get("domain"):
        print("The issue needs a client name and a domain.", file=sys.stderr)
        return 1
    json.dump(spec, open(sys.argv[1], "w"), indent=2)
    print("dry-run" if dry_run else "real-run")
    return 0


if __name__ == "__main__":
    sys.exit(main())

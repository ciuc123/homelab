#!/usr/bin/env python3
"""Turns an "SEO audit" issue form (or the manual-run inputs) into the parameters of an audit run.

The issue body and the inputs are untrusted text: they're only parsed and validated here, never executed or
interpolated into a shell. Only a public http(s) site is accepted: no IP literals, no localhost or internal
names, no credentials or custom ports, and the hostname must resolve to public addresses only.

Prints `key=value` lines for $GITHUB_OUTPUT: url (the site's origin), host, max_pages, client, slug.
Exits 2 with a message on stderr if the request is invalid."""

from __future__ import annotations

import argparse
import ipaddress
import re
import socket
import sys
from urllib.parse import urlsplit

from scripts.issue_to_spec import sections

DEFAULT_MAX_PAGES = 50
MAX_PAGES_LIMIT = 200
_HOST = re.compile(r"^(?=.{1,253}$)([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$")
_BLOCKED_SUFFIXES = (".local", ".localhost", ".internal", ".lan", ".home", ".corp", ".test", ".invalid", ".example")


class RequestError(ValueError):
    pass


def _resolve(host: str) -> list[str]:
    return sorted({info[4][0] for info in socket.getaddrinfo(host, None)})


def _is_ip(host: str) -> bool:
    try:
        ipaddress.ip_address(host)
        return True
    except ValueError:
        return False


def validate_url(raw: str, resolve=None) -> tuple[str, str]:
    """Returns (origin, host) for a public website, or raises RequestError."""
    resolve = resolve or _resolve
    raw = (raw or "").strip()
    if not raw:
        raise RequestError("The issue needs a target site.")
    if "://" not in raw:
        raw = "https://" + raw
    try:
        parts = urlsplit(raw)
        port = parts.port
    except ValueError as e:
        raise RequestError("Not a valid URL: %s" % e)
    if parts.scheme not in ("http", "https"):
        raise RequestError("Only http and https sites can be audited.")
    if parts.username or parts.password:
        raise RequestError("Don't put credentials in the URL.")
    if port not in (None, 80, 443):
        raise RequestError("Custom ports aren't allowed.")
    host = (parts.hostname or "").rstrip(".").lower()
    if _is_ip(host):
        raise RequestError("Use the site's domain name, not an IP address.")
    if not _HOST.match(host) or host.endswith(_BLOCKED_SUFFIXES):
        raise RequestError("%r isn't a public domain name." % host)
    try:
        addresses = resolve(host)
    except OSError:
        raise RequestError("%s doesn't resolve." % host)
    for a in addresses:
        if not ipaddress.ip_address(a.split("%")[0]).is_global:
            raise RequestError("%s resolves to a non-public address." % host)
    return "%s://%s" % (parts.scheme, host), host


def clean_max_pages(raw: str) -> int:
    raw = (raw or "").strip()
    if not raw:
        return DEFAULT_MAX_PAGES
    if not raw.isdigit():
        raise RequestError("Max pages must be a number.")
    return max(1, min(MAX_PAGES_LIMIT, int(raw)))


def clean_client(raw: str) -> str:
    """Free text for the report title: keep it to a safe character set and 60 characters."""
    text = re.sub(r"[^\w .,&'()-]", "", (raw or "").strip(), flags=re.UNICODE)
    return re.sub(r"\s+", " ", text)[:60].strip()


def parse(body: str) -> dict[str, str]:
    s = sections(body)
    return {"url": s.get("Target site", ""), "max_pages": s.get("Max pages", ""), "client": s.get("Client name", "")}


def build(url: str, max_pages: str, client: str, resolve=None) -> dict[str, str]:
    origin, host = validate_url(url, resolve)
    return {
        "url": origin,
        "host": host,
        "max_pages": str(clean_max_pages(max_pages)),
        "client": clean_client(client),
        "slug": host.replace(".", "-"),
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--url", help="manual run: target site (else the issue body is read from stdin)")
    p.add_argument("--max-pages", default="")
    p.add_argument("--client", default="")
    args = p.parse_args(argv)
    try:
        if args.url is not None:
            out = build(args.url, args.max_pages, args.client)
        else:
            req = parse(sys.stdin.read())
            out = build(req["url"], req["max_pages"], req["client"])
    except RequestError as e:
        print(str(e), file=sys.stderr)
        return 2
    for k, v in out.items():
        print("%s=%s" % (k, v))
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Minimal YAML front matter reader for Jekyll posts (stdlib has no YAML).

Supports what posts use: `key: value`, quoted strings, integers, inline lists `[a, b]`,
block lists (`- item`) and block scalars (`>`, `>-`, `|`, `|-`). Anything else is kept as the raw string.
"""
import re

_KEY = re.compile(r"^([A-Za-z_][\w-]*):(?:\s+(.*))?$")


class FrontMatterError(ValueError):
    pass


def split(text):
    """Return (front_matter_text, body). Raises FrontMatterError if there's no front matter block."""
    text = text.lstrip("﻿")
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        raise FrontMatterError("no front matter (file must start with ---)")
    for i in range(1, len(lines)):
        if lines[i].strip() in ("---", "..."):
            return "".join(lines[1:i]), "".join(lines[i + 1:])
    raise FrontMatterError("front matter is not closed with ---")


def _scalar(raw):
    raw = raw.strip()
    if not raw:
        return ""
    if raw[0] in "\"'" and raw[-1] == raw[0] and len(raw) >= 2:
        inner = raw[1:-1]
        return inner.replace('\\"', '"') if raw[0] == '"' else inner.replace("''", "'")
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        return [] if not inner else [_scalar(x) for x in _split_list(inner)]
    if re.fullmatch(r"-?\d+", raw):
        return int(raw)
    if raw in ("true", "false"):
        return raw == "true"
    return re.sub(r"\s+#.*$", "", raw)


def _split_list(inner):
    items, buf, quote = [], "", None
    for ch in inner:
        if quote:
            buf += ch
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
            buf += ch
        elif ch == ",":
            items.append(buf)
            buf = ""
        else:
            buf += ch
    items.append(buf)
    return [x.strip() for x in items if x.strip()]


_BLOCK = (">", ">-", "|", "|-")


def parse(fm_text):
    data, current, block = {}, None, None  # block: (key, style, lines)
    for n, line in enumerate(fm_text.splitlines(), 1):
        if block:
            if line.startswith((" ", "\t")) or not line.strip():
                block[2].append(line.strip())
                continue
            data[block[0]] = _join_block(block[1], block[2])
            block = None
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        stripped = line.strip()
        if stripped.startswith("- ") and current is not None:
            if not isinstance(data[current], list):
                data[current] = []
            data[current].append(_scalar(stripped[2:]))
            continue
        m = _KEY.match(line)
        if not m:
            raise FrontMatterError("line %d: can't parse %r" % (n, line))
        current = m.group(1)
        raw = (m.group(2) or "").strip()
        if raw in _BLOCK:
            block = (current, raw, [])
            data[current] = ""
        else:
            data[current] = _scalar(raw)
    if block:
        data[block[0]] = _join_block(block[1], block[2])
    return data


def _join_block(style, lines):
    while lines and not lines[-1]:
        lines.pop()
    if style.startswith("|"):
        return "\n".join(lines)
    out, para = [], []
    for l in lines:
        if l:
            para.append(l)
        else:
            out.append(" ".join(para))
            para = []
    out.append(" ".join(para))
    return "\n".join(p for p in out if p)


def read(path):
    with open(path, encoding="utf-8") as f:
        fm, body = split(f.read())
    return parse(fm), body

"""lint-content: front matter and body rules for Jekyll posts (_posts/*.md)."""
import datetime as dt
import os
import re

from . import frontmatter
from . import model as m

_FILENAME = re.compile(r"^(\d{4}-\d{2}-\d{2})-.+\.(md|markdown)$")
_YEAR = re.compile(r"\b((?:19|20)\d{2})\b(?!\.\d)")  # "in 2024" yes, "PhpStorm 2025.1" no
_FENCE = re.compile(r"^(```|~~~).*?^\1", re.S | re.M)


def word_count(body):
    text = _FENCE.sub(" ", body)
    text = re.sub(r"<[^>]+>|\{[%{].*?[%}]\}", " ", text)  # HTML tags, Liquid
    return len(re.findall(r"[A-Za-z0-9][\w'’.-]*", text))


def _date(value):
    s = str(value).strip()[:10]
    return dt.date.fromisoformat(s)


def lint_post(path, results, config, today):
    name = os.path.basename(path)
    target = "_posts/" + name
    try:
        fm, body = frontmatter.read(path)
    except (frontmatter.FrontMatterError, UnicodeDecodeError) as e:
        results.check(m.FRONT_MATTER, target, False, str(e))
        return
    title = str(fm.get("title", "")).strip()
    try:
        date = _date(fm.get("date")) if fm.get("date") else None
    except ValueError:
        date = None
    if not results.check(m.FRONT_MATTER, target, bool(title) and date is not None,
                         "missing or invalid title/date"):
        return

    results.check(m.TITLE_LENGTH, target, len(title) <= 60, "title is %d chars: %r" % (len(title), title))

    desc = str(fm.get("description", "") or "").strip()
    results.check(m.DESCRIPTION_PRESENT, target, bool(desc), "no description in front matter")
    if desc:
        results.check(m.DESCRIPTION_LENGTH, target, 120 <= len(desc) <= 160, "description is %d chars" % len(desc))

    tags = fm.get("tags")
    results.check(m.TAGS_PRESENT, target, isinstance(tags, list) and len(tags) > 0, "no tags")

    fn = _FILENAME.match(name)
    results.check(m.DATE_MATCHES_FILENAME, target, bool(fn) and fn.group(1) == date.isoformat(),
                  "filename date %s vs front matter date %s" % (fn.group(1) if fn else "missing", date))

    results.check(m.NO_FUTURE_DATE, target, date <= today, "dated %s, after %s" % (date, today))

    stale = [y for y in _YEAR.findall(title) if int(y) < date.year]
    results.check(m.STALE_YEAR, target, not stale, "title names %s but the post is dated %s" % (", ".join(stale), date))

    words = word_count(body)
    min_words = int(config.get("min_words", 300))
    results.check(m.MIN_WORDS, target, words >= min_words, "%d words (minimum %d)" % (words, min_words))

    if fm.get("last_modified_at"):
        try:
            mod = _date(fm["last_modified_at"])
            ok, msg = date <= mod <= today, "last_modified_at %s (post date %s)" % (mod, date)
        except ValueError:
            ok, msg = False, "last_modified_at isn't a date"
        results.check(m.LAST_MODIFIED, target, ok, msg)

    since = config.get("standard_since")
    if since and date >= _date(since):
        lint_standard(target, fm, body, results)


_HEADING = re.compile(r"^#{2,3}\s+(.+?)\s*#*\s*$", re.M)


def headings(body):
    return [h.strip() for h in _HEADING.findall(_FENCE.sub(" ", body))]


def lint_standard(target, fm, body, results):
    """The answer-first post standard (content-pipeline.md): takeaways, FAQ, question headings, sources."""
    tldr = fm.get("tldr")
    n = len(tldr) if isinstance(tldr, list) else 0
    results.check(m.POST_TLDR, target, 3 <= n <= 5 and all(str(x).strip() for x in tldr or []),
                  "%d takeaways (need 3-5)" % n)

    faq = fm.get("faq")
    if faq:
        bad = []
        for i, entry in enumerate(faq if isinstance(faq, list) else [faq], 1):
            q = str(entry.get("q", "")).strip() if isinstance(entry, dict) else ""
            a = str(entry.get("a", "")).strip() if isinstance(entry, dict) else ""
            if not q.endswith("?") or len(a.split()) < 20:
                bad.append(str(i))
        results.check(m.FAQ_ENTRIES, target, not bad, "entries %s need a question ending in ? and a 20+ word answer" % ", ".join(bad))

    hs = headings(body)
    results.check(m.QUESTION_HEADING, target, any(h.endswith("?") for h in hs), "no ## or ### heading ends with ?")
    results.check(m.SOURCES_SECTION, target, any(h.lower().rstrip(":") in ("sources", "references") for h in hs),
                  "no ## Sources section")


def lint_content(posts_dir, results, config, today=None):
    today = today or dt.date.today()
    files = sorted(f for f in os.listdir(posts_dir) if f.endswith((".md", ".markdown")))
    for f in files:
        lint_post(os.path.join(posts_dir, f), results, config, today)
    return len(files)

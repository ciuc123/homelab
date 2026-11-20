"""Console, JSON and Markdown output."""
import json
import re

from . import model as m
from .guidance import GUIDANCE, fix_order

MAX_LISTED = 25


def summary(results):
    return {
        "score": results.score(),
        "checks": len(results.active()),
        "passed": len(results.passes),
        "errors": len(results.errors),
        "warnings": len(results.warnings),
    }


def to_json(results, meta):
    return json.dumps({"meta": meta, "summary": summary(results), "rules": results.by_rule()}, indent=2)


def _sorted_rules(results):
    order = {m.ERROR: 0, m.WARNING: 1}
    return sorted(results.by_rule().items(), key=lambda kv: (kv[1]["failed"] == 0, order.get(kv[1]["severity"], 2), kv[0]))


def to_console(results, meta):
    s = summary(results)
    lines = ["SEO audit: %s %s" % (meta.get("mode"), meta.get("target")),
             "Score %(score)d/100 · %(checks)d checks · %(passed)d passed · %(errors)d errors · %(warnings)d warnings" % s, ""]
    for rule_id, r in _sorted_rules(results):
        if not r["failed"]:
            continue
        lines.append("%-7s %-24s %d failed / %d passed  %s" % (r["severity"].upper(), rule_id, r["failed"], r["passed"], m.RULES[rule_id].description))
        for f in r["failures"][:5]:
            lines.append("          %s: %s" % (f["target"], f["message"]))
        if r["failed"] > 5:
            lines.append("          … %d more" % (r["failed"] - 5))
    passing = [rid for rid, r in _sorted_rules(results) if not r["failed"]]
    if passing:
        lines += ["", "Passing: " + ", ".join(passing)]
    return "\n".join(lines)


def _delta(now, before):
    d = now - before
    return " (%+d)" % d if d else " (no change)"


def score_line(results, previous=None):
    s = summary(results)
    line = "**Score: %(score)d/100** · %(checks)d checks · %(passed)d passed · %(errors)d errors · %(warnings)d warnings" % s
    if previous:
        p = previous.get("summary", {})
        line += "  \nSince %s: score %d → %d%s" % (previous.get("meta", {}).get("date", "the last audit"),
                                                p.get("score", 0), s["score"], _delta(s["score"], p.get("score", 0)))
    return line


def _was(rule_id, previous):
    if not previous:
        return ""
    before = previous.get("rules", {}).get(rule_id, {}).get("failed", 0)
    return " (was %d)" % before


def md(text):
    """Show HTML tags literally in Markdown (GitHub would otherwise hide them)."""
    return re.sub(r"(<[^<>`]+>)", r"`\1`", text)


def _example(f, width=110):
    msg = f["message"]
    if len(msg) > width:
        msg = msg[: width - 1] + "…"
    return "`%s` (%s)" % (f["target"], md(msg.replace("`", "'"))) if msg else "`%s`" % f["target"]


def fix_first(results, previous=None, limit=None, examples=3):
    """Markdown list: failing rules by impact, with why, how and example targets."""
    by_rule = results.by_rule()
    out = []
    order = fix_order(by_rule)
    for i, rule_id in enumerate(order[:limit] if limit else order, 1):
        r = by_rule[rule_id]
        _, why, how = GUIDANCE[rule_id]
        ex = "; ".join(_example(f) for f in r["failures"][:examples])
        more = "; and %d more" % (r["failed"] - examples) if r["failed"] > examples else ""
        out.append("%d. **%s** — %d failing%s. %s  \n   **Fix:** %s  \n   Where: %s%s" % (
            i, md(m.RULES[rule_id].description), r["failed"], _was(rule_id, previous), md(why), md(how), ex, more))
    return out


def to_summary(results, meta, previous=None, report_url=None, limit=5):
    """Short Markdown for an issue comment or a job summary."""
    title = meta.get("title") or meta.get("target")
    out = ["## SEO audit: %s" % title, "", score_line(results, previous), ""]
    items = fix_first(results, previous, limit=limit)
    if items:
        total = len(fix_order(results.by_rule()))
        out += ["### What to fix first%s" % (" (top %d of %d)" % (limit, total) if total > limit else ""), ""] + items
    else:
        out.append("Every check passed.")
    if report_url:
        out += ["", "Full report: %s" % report_url]
    return "\n".join(out) + "\n"


def to_markdown(results, meta, previous=None):
    title = meta.get("title")
    out = ["# SEO audit report" + (": %s" % title if title else ""), "",
           "- **Mode:** `%s`  **Target:** `%s`" % (meta.get("mode"), meta.get("target")),
           "- **Date:** %s  **Tool:** seo_audit %s" % (meta.get("date"), meta.get("version")), "",
           score_line(results, previous), ""]
    items = fix_first(results, previous)
    if items:
        out += ["## What to fix first", "", "Ordered by impact: lost visitors and leads first, then how the site shows up in "
                "search, social and AI answers, then polish.", ""] + items + [""]
    out += ["## All checks", "",
            "| Rule | Severity | Failed | Passed | What it checks |", "|---|---|---:|---:|---|"]
    for rule_id, r in _sorted_rules(results):
        mark = "✅" if not r["failed"] else ("❌" if r["severity"] == m.ERROR else "⚠️")
        out.append("| %s `%s` | %s | %d | %d | %s |" % (mark, rule_id, r["severity"], r["failed"], r["passed"], md(m.RULES[rule_id].description)))
    failing = [(rid, r) for rid, r in _sorted_rules(results) if r["failed"]]
    if failing:
        out += ["", "## Failures"]
        for rule_id, r in failing:
            out += ["", "### `%s` (%s, %d)" % (rule_id, r["severity"], r["failed"])]
            for f in r["failures"][:MAX_LISTED]:
                out.append("- `%s`: %s" % (f["target"], f["message"].replace("|", "\\|")))
            if r["failed"] > MAX_LISTED:
                out.append("- … %d more (see the JSON report)" % (r["failed"] - MAX_LISTED))
    return "\n".join(out) + "\n"

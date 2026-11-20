"""Rules, results and scoring."""
from dataclasses import dataclass

ERROR, WARNING, OFF = "error", "warning", "off"


@dataclass(frozen=True)
class Rule:
    id: str
    severity: str  # default severity; .seo-audit.json can override it
    description: str


RULES = {}


def rule(rule_id, severity, description):
    RULES[rule_id] = Rule(rule_id, severity, description)
    return rule_id


# Content (source posts)
FRONT_MATTER = rule("front-matter", ERROR, "Post has parseable front matter with title and date")
TITLE_LENGTH = rule("title-length", ERROR, "Post title is 60 characters or fewer")
DESCRIPTION_PRESENT = rule("description-present", ERROR, "Post front matter has a description")
DESCRIPTION_LENGTH = rule("description-length", ERROR, "Post description is 120-160 characters")
TAGS_PRESENT = rule("tags-present", ERROR, "Post has at least one tag")
DATE_MATCHES_FILENAME = rule("date-matches-filename", ERROR, "Front matter date matches the YYYY-MM-DD filename prefix")
NO_FUTURE_DATE = rule("no-future-date", ERROR, "Post date is not in the future")
STALE_YEAR = rule("stale-year-in-title", ERROR, "Title doesn't name a year older than the post date")
MIN_WORDS = rule("min-word-count", ERROR, "Post body has at least min_words words (code blocks excluded)")

# Rendered pages
SINGLE_TITLE = rule("single-title", ERROR, "Page has exactly one non-empty <title>")
META_DESCRIPTION = rule("meta-description", ERROR, "Page has a meta description")
META_DESCRIPTION_LENGTH = rule("meta-description-length", ERROR, "Meta description is 50-160 characters")
CANONICAL = rule("canonical", ERROR, "Page has an absolute canonical URL")
SINGLE_H1 = rule("single-h1", ERROR, "Page has exactly one <h1>")
JSON_LD_VALID = rule("json-ld-valid", ERROR, "Every JSON-LD block parses")
JSON_LD_PRESENT = rule("json-ld-present", ERROR, "Page has structured data (JSON-LD)")
OG_IMAGE = rule("og-image", ERROR, "Page has og:image")
IMG_ALT = rule("img-alt", ERROR, "Every <img> has an alt attribute")
INTERNAL_LINKS = rule("internal-links", ERROR, "Internal links point to pages that exist")
POST_CTA = rule("post-cta", ERROR, "Every post has a call to action (.post-cta)")
FORM_ACTION = rule("form-action", ERROR, "Every <form> posts to a real endpoint (non-empty action)")

# Whole site
ROBOTS_TXT = rule("robots-txt", ERROR, "robots.txt exists and names the sitemap")
SITEMAP = rule("sitemap", ERROR, "sitemap.xml exists and parses")
SITEMAP_URLS = rule("sitemap-urls-exist", ERROR, "Every sitemap URL resolves to a page")
LLMS_TXT = rule("llms-txt", ERROR, "llms.txt exists and isn't empty")
PRIVATE_FILES = rule("private-files", ERROR, "Private repo files aren't published")
ORPHAN_PAGES = rule("orphan-pages", ERROR, "Every sitemap page is linked from another page")


class Results:
    """Collects every check (pass or fail). Severity comes from config overrides or the rule default."""

    def __init__(self, overrides=None):
        self.overrides = overrides or {}
        self.checks = []  # (rule_id, target, passed, message)
        unknown = set(self.overrides) - set(RULES)
        if unknown:
            raise ValueError("Unknown rule id(s) in config: " + ", ".join(sorted(unknown)))

    def severity(self, rule_id):
        return self.overrides.get(rule_id, RULES[rule_id].severity)

    def check(self, rule_id, target, passed, message=""):
        if rule_id not in RULES:
            raise KeyError(rule_id)
        self.checks.append((rule_id, target, bool(passed), "" if passed else message))
        return passed

    def active(self):
        return [c for c in self.checks if self.severity(c[0]) != OFF]

    def failures(self, severity=None):
        return [c for c in self.active() if not c[2] and (severity is None or self.severity(c[0]) == severity)]

    @property
    def errors(self):
        return self.failures(ERROR)

    @property
    def warnings(self):
        return self.failures(WARNING)

    @property
    def passes(self):
        return [c for c in self.active() if c[2]]

    def score(self):
        """Share of active checks that pass, 0-100. Errors and warnings count the same."""
        active = self.active()
        return 100 if not active else round(100 * len(self.passes) / len(active))

    def by_rule(self):
        out = {}
        for rule_id, target, passed, message in self.active():
            r = out.setdefault(rule_id, {"severity": self.severity(rule_id), "passed": 0, "failed": 0, "failures": []})
            if passed:
                r["passed"] += 1
            else:
                r["failed"] += 1
                r["failures"].append({"target": target, "message": message})
        return out

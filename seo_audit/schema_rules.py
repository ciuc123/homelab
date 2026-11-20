"""JSON-LD and robots.txt helpers for the entity, article-author and AI-crawler rules."""
import json

ENTITY_TYPES = {
    "Person", "Organization", "Corporation", "LocalBusiness", "ProfessionalService", "OnlineBusiness", "OnlineStore",
    "Store", "NGO", "EducationalOrganization", "MedicalOrganization", "MedicalBusiness", "LegalService",
    "FinancialService", "HealthAndBeautyBusiness", "HomeAndConstructionBusiness", "FoodEstablishment", "Restaurant",
    "AutomotiveBusiness", "SportsActivityLocation", "EntertainmentBusiness", "LodgingBusiness", "TravelAgency",
    "Dentist", "Physician", "Attorney", "AccountingService", "RealEstateAgent", "ProfessionalService",
}
ARTICLE_TYPES = {"Article", "BlogPosting", "NewsArticle", "TechArticle", "Report", "ScholarlyArticle"}

# Crawlers that put a site into search results or AI answers. Blocking these costs visibility.
# (Training-only crawlers such as GPTBot, ClaudeBot, Google-Extended or CCBot are a policy choice, not checked.)
SEARCH_AND_ANSWER_BOTS = ["Googlebot", "Bingbot", "OAI-SearchBot", "ChatGPT-User", "Claude-SearchBot", "Claude-User",
                          "PerplexityBot", "Perplexity-User", "DuckDuckBot", "Applebot"]


def nodes(raw_blocks):
    """All JSON-LD objects from the page's blocks, flattening lists and @graph. Invalid blocks are skipped."""
    out = []

    def walk(x):
        if isinstance(x, list):
            for i in x:
                walk(i)
        elif isinstance(x, dict):
            out.append(x)
            if "@graph" in x:
                walk(x["@graph"])

    for raw in raw_blocks:
        try:
            walk(json.loads(raw))
        except ValueError:
            pass
    return out


def types(node):
    t = node.get("@type", [])
    return set(t if isinstance(t, list) else [t])


def entity_problem(raw_blocks):
    """None if a Person/Organization-like node has a name and sameAs links, else why not."""
    entities = [n for n in nodes(raw_blocks) if types(n) & ENTITY_TYPES]
    if not entities:
        return "no Person or Organization in JSON-LD"
    for n in entities:
        same = n.get("sameAs")
        if n.get("name") and same and (isinstance(same, str) or len(same) > 0):
            return None
    return "Person/Organization without name and sameAs (profile links)"


def articles_without_author(raw_blocks):
    """(number of article nodes, number without an author)."""
    arts = [n for n in nodes(raw_blocks) if types(n) & ARTICLE_TYPES]
    missing = 0
    for n in arts:
        a = n.get("author")
        if isinstance(a, list):
            a = a[0] if a else None
        if not (isinstance(a, str) and a.strip()) and not (isinstance(a, dict) and (a.get("name") or a.get("@id"))):
            missing += 1
    return len(arts), missing


def robots_groups(text):
    """[(set of lowercased user-agents, [(directive, path)])], following the robots.txt grouping rules."""
    groups, agents, rules, last = [], [], [], None
    for line in text.splitlines():
        line = line.split("#", 1)[0].strip()
        if ":" not in line:
            continue
        key, value = (x.strip() for x in line.split(":", 1))
        key = key.lower()
        if key == "user-agent":
            if last == "rule":
                groups.append((set(agents), rules))
                agents, rules = [], []
            agents.append(value.lower())
            last = "agent"
        elif key in ("allow", "disallow") and agents:
            rules.append((key, value))
            last = "rule"
    if agents:
        groups.append((set(agents), rules))
    return groups


def blocked_bots(robots_text, bots=SEARCH_AND_ANSWER_BOTS):
    """Bots whose applicable robots.txt group disallows the whole site."""
    groups = robots_groups(robots_text)
    blocked = []
    for bot in bots:
        token = bot.lower()
        specific = [r for a, r in groups if token in a]
        applicable = specific or [r for a, r in groups if "*" in a]
        for rules in applicable:
            disallow_all = any(d == "disallow" and p == "/" for d, p in rules)
            allow_root = any(d == "allow" and p in ("/", "/*") for d, p in rules)
            if disallow_all and not allow_root:
                blocked.append(bot)
                break
    return blocked

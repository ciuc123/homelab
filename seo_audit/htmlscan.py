"""Extracts what the page rules need from an HTML document, using only html.parser."""
from html.parser import HTMLParser


class PageScan(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.titles = []        # text of each <title> in <head>
        self.metas = []         # attribute dicts
        self.links = []         # <link> attribute dicts
        self.h1_count = 0
        self.jsonld = []        # raw JSON-LD strings
        self.imgs = []          # <img> attribute dicts
        self.anchors = []       # href values
        self.forms = []         # <form> attribute dicts
        self.classes = set()
        self._in_head = False
        self._title_buf = None
        self._ld_buf = None

    def handle_starttag(self, tag, attrs):
        a = {k: (v if v is not None else "") for k, v in attrs}
        for c in a.get("class", "").split():
            self.classes.add(c)
        if tag == "head":
            self._in_head = True
        elif tag == "title" and self._in_head:
            self._title_buf = ""
        elif tag == "meta":
            self.metas.append(a)
        elif tag == "link":
            self.links.append(a)
        elif tag == "h1":
            self.h1_count += 1
        elif tag == "script" and a.get("type", "").lower() == "application/ld+json":
            self._ld_buf = ""
        elif tag == "img":
            self.imgs.append(a)
        elif tag == "a" and "href" in a:
            self.anchors.append(a["href"])
        elif tag == "form":
            self.forms.append(a)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag == "head":
            self._in_head = False
        elif tag == "title" and self._title_buf is not None:
            self.titles.append(self._title_buf.strip())
            self._title_buf = None
        elif tag == "script" and self._ld_buf is not None:
            self.jsonld.append(self._ld_buf)
            self._ld_buf = None

    def handle_data(self, data):
        if self._title_buf is not None:
            self._title_buf += data
        if self._ld_buf is not None:
            self._ld_buf += data

    # convenience accessors
    def meta(self, name=None, prop=None):
        for m in self.metas:
            if name and m.get("name", "").lower() == name:
                return m.get("content")
            if prop and m.get("property", "").lower() == prop:
                return m.get("content")
        return None

    def canonical(self):
        for l in self.links:
            if "canonical" in l.get("rel", "").lower().split():
                return l.get("href")
        return None


def scan(html):
    p = PageScan()
    p.feed(html)
    p.close()
    return p

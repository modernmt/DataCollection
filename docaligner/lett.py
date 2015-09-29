import base64
from collections import namedtuple

Page = namedtuple("Page", "url, html, text, mime_type, encoding")


def read_lett(f, slang, tlang):
    s, t = {}, {}
    for line in f:
        lang, mine, enc, url, html, text = line.strip().split("\t")
        html = base64.b64decode(html).decode("utf-8")
        text = base64.b64decode(text).decode("utf-8")
        assert lang in [slang, tlang]
        p = Page(url, html, text, mine, enc)
        if lang == slang:
            s[url] = p
        else:
            t[url] = p
    return s, t

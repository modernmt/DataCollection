import base64
from collections import namedtuple

Page = namedtuple(
    "Page", "url, html, text, mime_type, encoding")


def read_lett(f, slang, tlang, source_tokenizer=None, target_tokenizer=None):
    s, t = {}, {}
    for line in f:
        lang, mine, enc, url, html, text = line.strip().split("\t")
        html = base64.b64decode(html).decode("utf-8")
        text = base64.b64decode(text).decode("utf-8")
        # assert lang in [slang, tlang]

        if lang == slang and source_tokenizer is not None:
            text = source_tokenizer.process(text)
        elif lang == tlang and target_tokenizer is not None:
            text = target_tokenizer.process(text)
        else:
            # ignore other languages
            continue

        p = Page(url, html, text, mine, enc)
        if lang == slang:
            s[url] = p
        elif lang == tlang:
            t[url] = p
    return s, t


def write_tokenized_lett(f, pages):
    for p in pages:
        html = p.html.encode("utf-8")

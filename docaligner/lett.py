import base64
import gzip
from collections import namedtuple

Page = namedtuple(
    "Page", "url, html, text, mime_type, encoding")


def read_lett(f, slang, tlang, source_tokenizer=None, target_tokenizer=None,
              no_html=False):
    s, t = {}, {}
    fh = f
    if f.name.endswith('.gz'):
        fh = gzip.open(fh, 'r')
    for line in fh:
        lang, mine, enc, url, html, text = line.strip().split("\t")

        if no_html:
            html = ''
        else:
            html = base64.b64decode(html)

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
    pass

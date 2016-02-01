import base64
import gzip
import sys
from collections import namedtuple

Page = namedtuple(
    "Page", "url, html, text, mime_type, encoding")


def read_lett(f, slang, tlang, source_tokenizer=None, target_tokenizer=None,
              no_html=False):
    s, t = {}, {}
    fh = f
    if f.name.endswith('.gz'):
        fh = gzip.GzipFile(fileobj=fh, mode='r')
    for line in fh:
        lang, mine, enc, url, html, text = line[:-1].split("\t")

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

        p = Page(url, html, text, mine, enc)
        if lang == slang:
            s[url] = p
        elif lang == tlang:
            t[url] = p
    return s, t


def write_tokenized_lett(f, pages):
    pass

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'lettfile', help='input lett file', type=argparse.FileType('r'))
    parser.add_argument('-slang', help='source language', default='en')
    parser.add_argument('-tlang', help='target language', default='fr')
    args = parser.parse_args()

    # read source and target corpus
    s, t = read_lett(args.lettfile, args.slang, args.tlang)

    sys.stderr.write("Read %d %s docs and %d %s docs from %s\n" %
                     (len(s), args.slang,
                      len(t), args.tlang, args.lettfile.name))
    sys.stderr.write("%d possible pairs for %s\n" %
                     (len(s) * len(t), args.lettfile.name))

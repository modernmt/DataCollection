#!/usr/bin/env python
# -*- coding: utf-8 -*-
import base64
import sys

from html2text import html2text
from textsanitzer import TextSanitizer

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-n',
                        help='line number to extract', type=int, default=0)
    parser.add_argument(
        '-fromhtml', help='re-extract text from HTML', action='store_true')

    args = parser.parse_args()

    for linenr, line in enumerate(sys.stdin):
        if linenr > args.n:
            break
        elif linenr < args.n:
            continue

        lang, mime_type, enc, uri, html, text = line.split("\t")
        uri = TextSanitizer.to_unicode(uri)

        if args.fromhtml:
            text = html2text(base64.b64decode(html), sanitize=False,
                             ignore_br=False)
        else:
            text = base64.b64decode(text).decode("utf-8")

        html = base64.b64decode(html).decode('utf-8')

        print uri.encode('utf-8')
        print "\n---HTML---\n\n"
        print html.encode('utf-8')
        print "\n---TEXT---\n\n"
        print text.encode("utf-8")

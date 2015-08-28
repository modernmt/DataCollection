#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import base64
from html2text import html2text

magic_numer = "df6fa1abb58549287111ba8d776733e9"


def process_buffer(buf, d):
    if not buf:
        return
    header = buf[0]
    url = header.split()[1]
    skip = 0
    empty_lines = 0
    while empty_lines < 2:
        skip += 1
        if not buf[skip].strip():
            empty_lines += 1
    html = "".join(buf[skip + 1:])
    d[url] = (header, html)


def read_file(f, d):
    buf = []
    for line in f:
        if line.startswith(magic_numer):
            process_buffer(buf, d)
            buf = [line]
            continue
        buf.append(line)
    process_buffer(buf, d)


def process_dict(d):
    for u, (header, html) in d.iteritems():
        original_url = header.split()[2]
        text = hmtl2text(html, sanitize=True)
        # html = base64.b64encode(html.encode("utf-8"))
        yield u, original_url, html, text


def write_lett(sdict, tdict, slang, tlang, f):
    mime_type = "text/html"
    encoding = "charset=utf-8"
    for l, d in ((slang, sdict), (tlang, tdict)):
        for url, original_url, html, text in process_dict(d):
            f.write("{l}\t{mime}\t{enc}\t{name}\t{html}\t{text}\n".format(
                l=l,
                mime=mime_type,
                enc=encoding,
                name=original_url,
                html=base64.b64encode(html),
                text=base64.b64encode(text.encode("utf-8"))))
        # html=base64.b64encode(html.encode("utf-8")),
        # text=base64.b64encode(text.encode("utf-8"))))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=argparse.FileType('r'),
                        help='source corpus')
    parser.add_argument('target', type=argparse.FileType('r'),
                        help='target corpus')
    parser.add_argument('outfile', type=argparse.FileType('w'),
                        help='output file')
    parser.add_argument('-slang', help='source language', default='en')
    parser.add_argument('-tlang', help='target language', default='fr')
    args = parser.parse_args(sys.argv[1:])

    sdict, tdict = {}, {}
    read_file(args.source, sdict)
    read_file(args.target, tdict)
    write_lett(sdict, tdict, args.slang, args.tlang, args.outfile)

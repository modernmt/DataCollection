#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import base64
import html5lib
import re
from html5lib import treebuilders, treewalkers


magic_numer = "df6fa1abb58549287111ba8d776733e9"

# from: https://developer.mozilla.org/en-US/docs/Web/HTML/Block-level_elements
block_level_elements = set([u'address', u'article', u'aside', u'audio',
                            u'blockquote', u'canvas', u'dd', u'div', u'dl',
                            u'fieldset', u'figcaption', u'figure', u'footer',
                            u'form', u'h1', u'h2', u'h3', u'h4', u'h5', u'h6',
                            u'header', u'hgroup', u'hr', u'noscript', u'ol',
                            u'output', u'p', u'pre', u'section', u'table',
                            u'tfoot', u'ul', u'video'])


def clean_whitespace(s):
    # remove empty lines
    s = [l.strip() for l in s.split("\n") if l.strip()]
    return "\n".join(re.sub("\s+", " ", l) for l in s)


def hmtl2text(html):
    p = html5lib.HTMLParser(tree=treebuilders.getTreeBuilder("dom"))
    dom_tree = p.parse(html.decode("utf-8"))
    walker = treewalkers.getTreeWalker("dom")
    stream = walker(dom_tree)

    in_script = False
    outbuf = []
    current_line = []
    for token in stream:
        token_name = token.get('name', "").lower()

        if token_name in ['script', 'style', 'noscript']:
            in_script = token.get('type', None) == 'StartTag'
        if in_script:
            continue

        if token_name in block_level_elements or token_name == "br":
            if current_line:
                outbuf.append(u"".join(current_line))
                current_line = []

        if token.get(u'type', None) == u'Characters':
            current_line.append(token['data'])
        if token.get(u'type', None) == u'SpaceCharacters':
            if current_line and current_line[-1] != u" ":
                current_line.append(u" ")

    if current_line:
        outbuf.append(u"".join(current_line))
    return clean_whitespace("\n".join(outbuf))


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
        text = hmtl2text(html)
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

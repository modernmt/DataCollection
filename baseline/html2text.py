#!/usr/bin/env python
# -*- coding: utf-8 -*-

import html5lib
import sys
from textsanitzer import TextSanitizer
from html5lib import treebuilders, treewalkers

""" Utility functions to extract text from a website """

# from: https://developer.mozilla.org/en-US/docs/Web/HTML/Block-level_elements
block_level_elements = set([u'address', u'article', u'aside', u'audio',
                            u'blockquote', u'canvas', u'dd', u'div', u'dl',
                            u'fieldset', u'figcaption', u'figure', u'footer',
                            u'form', u'h1', u'h2', u'h3', u'h4', u'h5', u'h6',
                            u'header', u'hgroup', u'hr', u'noscript', u'ol',
                            u'output', u'p', u'pre', u'section', u'table',
                            u'tfoot', u'ul', u'video'])


def html2text(html):
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

        # This technically violates the standard as spans
        # don't introduce whitespace. In practice whitespace
        # is often added via CSS and spans rarely end in the
        # middle of a word.
        if token_name == 'span':
            current_line.append(u" ")

        if token.get(u'type', None) == u'Characters':
            current_line.append(token['data'])
        if token.get(u'type', None) == u'SpaceCharacters':
            if current_line and current_line[-1] != u" ":
                current_line.append(u" ")

        if token_name == 'span':
            current_line.append(u" ")

    if current_line:
        outbuf.append(u"".join(current_line))
    return TextSanitizer.clean_whitespace("\n".join(outbuf))


if __name__ == "__main__":
    buffer = []
    for line in sys.stdin:
        buffer.append(line)
    html = "".join(buffer)
    text = html2text(html)
    sys.stdout.write(text.encode('utf-8'))
    sys.stdout.write("\n")

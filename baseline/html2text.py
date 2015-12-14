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


def html2text(html, sanitize=False, ignore_br=False):
    """ Takes utf-8 encoded page and returns unicode text """
    p = html5lib.HTMLParser(tree=treebuilders.getTreeBuilder("dom"))
    dom_tree = p.parse(html.decode("utf-8"))
    walker = treewalkers.getTreeWalker("dom")
    stream = walker(dom_tree)

    space_introducing_tags = set(['th', 'td'])
    # Add space around spans
    # This technically violates the standard as spans
    # don't introduce whitespace. In practice whitespace
    # is often added via CSS and spans rarely end in the
    # middle of a word.
    space_introducing_tags.add('span')

    line_break_tags = block_level_elements
    line_break_tags.add('tr')  # <tr> introduces line-break
    line_break_tags.add('li')  # <li> introduces line-break
    line_break_tags.add('option')  # <option> introduces line-break

    if ignore_br:
        space_introducing_tags.add('br')
    else:
        line_break_tags.add('br')

    in_script = False
    outbuf = []
    current_line = []
    for token in stream:
        token_name = token.get('name', "").lower()

        # ignore everything in scripts
        if token_name in ['script', 'style', 'noscript']:
            in_script = token.get('type', None) == 'StartTag'
        if in_script:
            continue

        # Should we start a new line?
        if token_name in line_break_tags:
            if current_line:
                outbuf.append(u"".join(current_line))
                current_line = []

        # Add space before data
        if token_name in space_introducing_tags:
            current_line.append(u" ")

        if token.get(u'type', None) == u'Characters':
            current_line.append(
                TextSanitizer.clean_whitespace(token['data'],
                                               linesep=u' '))

        # Unify any space to standard spaces
        if token.get(u'type', None) == u'SpaceCharacters':
            if current_line and current_line[-1] != u' ':
                current_line.append(u' ')

        # Add space after data
        if token_name in space_introducing_tags:
            current_line.append(u' ')

    if current_line:
        outbuf.append(u"".join(current_line))

    text = u"\n".join(outbuf)
    text = TextSanitizer.clean_text(
        text, sanitize=sanitize, clean_whitespace=True)
    return text


if __name__ == "__main__":
    buffer = []
    for line in sys.stdin:
        buffer.append(line)
    html = "".join(buffer)
    text = html2text(html)
    sys.stdout.write(text.encode('utf-8'))
    sys.stdout.write("\n")

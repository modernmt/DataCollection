#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import base64

""" Makes bitextors .docs files humand readable """

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-html', help='show HTML', action='store_true')
    args = parser.parse_args()

    for line in sys.stdin:
        line = line.strip().split("\t")
        s_url, t_url, source, target = line[:4]

        src_html, tgt_html = '', ''

        # for reading .down files
        if len(line) == 6:
            src_html = base64.b64decode(line[4])
            # print line[5]
            tgt_html = base64.b64decode(line[5])

        source = base64.b64decode(source)
        target = base64.b64decode(target)

        sys.stdout.write("----------------")
        sys.stdout.write("Source URL: %s\n" % s_url)
        sys.stdout.write("Target URL: %s\n" % s_url)
        sys.stdout.write("---SOURCE TEXT ---\n\n%s\n" % source)
        if src_html and args.html:
            sys.stdout.write("---SOURCE HTML ---\n\n%s\n" % src_html)
        sys.stdout.write("---TARGET TEXT ---\n\n%s\n" % target)
        if tgt_html and args.html:
            sys.stdout.write("---TARGET HTML ---\n\n%s\n" % tgt_html)

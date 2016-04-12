#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from itertools import izip
import locale
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-source', type=argparse.FileType('r'),
                        help='sources of translations', required=True)
    parser.add_argument('-target', type=argparse.FileType('r'),
                        help='translation of source', required=True)
    parser.add_argument('-outfile', type=argparse.FileType('w'),
                        help='output file for translated segments')
    parser.add_argument('-outfile_source', type=argparse.FileType('w'),
                        help='output file for untranslated segments')
    args = parser.parse_args(sys.argv[1:])

    s2t = {}
    for s, t in izip(args.source, args.target):
        s = s.rstrip('\n').decode('utf-8')
        t = t.rstrip('\n').decode('utf-8')
        s2t[s] = t
    print "Read %d pairs" % len(s2t)
    print "Last:", s, t

    fixes = {}

    for linenr, line in enumerate(sys.stdin):
        filename, text = line.rstrip('\n').split('\t', 1)
        text = text.strip().decode('utf-8')

        # text = text.strip()
        if text not in s2t:
            if text in fixes:
                text = fixes[text]
            else:
                for s in s2t:
                    if locale.strcoll(text, s) == 0:
                        fixes[text] = s
                        print "fixed: %s -> %s" % (repr(text), repr(s))
                        text = s
                        break

        if text not in s2t:
            print "Text for file %s not found" % filename
            print "Text: %s" % repr(text)
            continue

        if args.outfile:
            args.outfile.write(
                "%s\t%s\n" % (filename, s2t[text].encode('utf-8')))
        if args.outfile_source:
            args.outfile_source.write(
                "%s\t%s\n" % (filename2url[filename], text.encode('utf-8')))

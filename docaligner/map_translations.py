#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from itertools import izip
import locale
locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-mappings', type=argparse.FileType('r'), nargs='+',
                        help='filename-to-url mappings', required=True)
    parser.add_argument('-brokenuris', type=argparse.FileType('r'),
                        help='uris that got mangled when extracting text')
    parser.add_argument('-source', type=argparse.FileType('r'),
                        help='sources of translations', required=True)
    parser.add_argument('-target', type=argparse.FileType('r'),
                        help='translation of source', required=True)
    parser.add_argument('-outfile', type=argparse.FileType('w'),
                        help='output file for translated segments')
    parser.add_argument('-outfile_source', type=argparse.FileType('w'),
                        help='output file for untranslated segments')
    # parser.add_argument('-prefix', help='prefix added to make filenames',
    #                     default="/fs/syn0/pkoehn/crawl/data/site-crawls")
    # parser.add_argument('-lang', help='non-english language', default='fr')
    # parser.add_argument(
    #     '-splitter', help='moses sentence splitting script',
    #     default="/home/buck/net/build/moses-clean/scripts/ems/support/split-sentences.perl")
    # parser.add_argument(
    #     '-normalizer', help='moses normalization script',
    #     default="/home/buck/net/build/moses-clean/scripts/tokenizer/normalize-punctuation.perl")
    # parser.add_argument(
    #     '-tokenizer', help='moses tokenization script',
    #     default="/home/buck/net/build/moses-clean/scripts/tokenizer/tokenizer.perl")
    # parser.add_argument('-langsplit', help='langsplit executable',
    #                     default="/home/buck/net/build/mtma_bitext/html_convert/langsplit")
    # parser.add_argument(
    #     '-fromhtml', help='re-extract text from HTML', action='store_true')

    args = parser.parse_args(sys.argv[1:])

    filename2url = dict()
    for fh in args.mappings:
        for line in fh:
            filename, url = line[:-1].split('\t')
            assert filename not in filename2url
            filename2url[filename] = url

    broken2filename = {}
    if args.brokenuris:
        for line in args.brokenuris:
            broken, normal = line[:-1].split('\t')
            broken2filename[broken] = normal

    s2t = {}
    for s, t in izip(args.source, args.target):
        s = s.strip().decode('utf-8')
        s2t[s.strip()] = t.rstrip('\n')
    print "Read %d pairs" % len(s2t)

    n_files = 0
    fixes = {}

    for linenr, line in enumerate(sys.stdin):
        n_files += 1
        filename, text = line[:-1].split('\t', 1)
        text = text.strip().decode('utf-8')

        if filename in broken2filename:
            filename = broken2filename[filename]

        if filename not in filename2url:
            print "No found:", filename
            sys.exit()

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
                "%s\t%s\n" % (filename2url[filename], s2t[text]))
        if args.outfile_source:
            args.outfile_source.write(
                "%s\t%s\n" % (filename2url[filename], text.encode('utf-8')))

    print "found all %d filenames" % n_files

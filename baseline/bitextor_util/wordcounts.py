#!/usr/bin/env python

import sys
import codecs
from collections import defaultdict
from bitextorutil import read_lett

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('lett', help='bitextor lett file')
    parser.add_argument('-lang1',
                        help='Two letter source language code', required=True)
    parser.add_argument('-lang2',
                        help='Two letter target language code', required=True)
    parser.add_argument('-m', help='Max number of occurences to keep word',
                        type=int, default=-1)
    parser.add_argument('-once', help='count only once per document',
                        action='store_true')

    args = parser.parse_args(sys.argv[1:])
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout)

    counts_l1, counts_l2 = defaultdict(int), defaultdict(int)
    for linenr, lang, words in read_lett(args.lett, as_set=args.once):
        for w in words:
            # w = w.encode('utf-8')`
            if lang == args.lang1:
                counts_l1[w] += 1
            elif lang == args.lang2:
                counts_l2[w] += 1

    for w, count in counts_l1.iteritems():
        if args.m <= 0 or count <= args.m:
            sys.stdout.write("%s\t%d\t%s\n" % (args.lang1, count, w))
    for w, count in counts_l2.iteritems():
        if args.m <= 0 or count <= args.m:
            sys.stdout.write("%s\t%d\t%s\n" % (args.lang2, count, w))

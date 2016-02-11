#!/usr/bin/env python
# -*- coding: utf-8 -*-
from collections import defaultdict
import math
import sys

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('counts', help='input counts file',
                        type=argparse.FileType('r'), nargs='+')
    parser.add_argument(
        '-outfile', help='output file', type=argparse.FileType('w'),
        default=sys.stdout)
    parser.add_argument('-lower', help='lowercase ngrams',
                        action='store_true', default=False)
    parser.add_argument('-mincount', help='minimum count', type=int, default=2)
    args = parser.parse_args(sys.argv[1:])

    counts = defaultdict(int)
    n_docs = 0

    for f in args.counts:
        n_docs += int(f.readline())
        for line in f:
            ngram, count = line.split('\t')
            if args.lower:
                ngram = ngram.lower()
            counts[ngram] += int(count)

    args.outfile.write("%d\n" % (n_docs))
    n_written, n_skipped = 0, 0
    for ngram, count in counts.iteritems():
        if count < args.mincount:
            n_skipped += 1
            continue
        idf = math.log(float(n_docs)) - math.log(float(count))
        args.outfile.write("%s\t%d\t%f\n" % (ngram, count, idf))
        n_written += 1

    sys.stderr.write("Wrote %d and skipped %d due to count below %d\n" %
                     (n_written, n_skipped, args.mincount))

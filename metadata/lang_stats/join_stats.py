#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from collections import defaultdict
from itertools import izip
from math import log

""" join language stat files together, possibly
    filtering by langauge

    input data are several file of format

    [entropy] domain l1 b1 [l2 b2 [l3 b3 [...]]]
    where
    * ln is a language identifier and
    * bn is the number of byes in that language
    * entropy is optional and ignored

    Example:
    -0.000089 www.hammockforums.net en 22430509 da 155

    Output is in the same format
"""


def entropy(lang_dist):
    total = float(sum(lang_dist.values()))
    h = 0

    if total <= 0:
        sys.stderr.write("weird values: total: %f\n" % total)
        return h

    for lang, count in lang_dist.iteritems():
        p = float(count) / total
        try:
            h += p * log(p)
        except ValueError:
            sys.stderr.write("weird values: cnt: %d, total: %f\n"
                             % (count, total))
            return 0
    return h


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('infiles', nargs='+', help="statistics files",
                        type=argparse.FileType('r'))
    parser.add_argument('-lang', nargs='*',
                        help="Ignore all other languages but these.")
    parser.add_argument('-nomono', action='store_true',
                        help='filter monolingual entries')
    parser.add_argument('-total', action='store_true',
                        help='ignore domains')
    args = parser.parse_args()

    valid_languages = None
    if args.lang:
        valid_languages = [l.lower() for l in args.lang]

    stats = defaultdict(lambda: defaultdict(int))

    for f in args.infiles:
        for line in f:
            data = line.split()
            if len(data) % 2 == 0:  # Line contrains entropy in first column
                _entropty = data.pop(0)
            domain = data.pop(0)
            domain = domain.split('?')[0]
            if args.total:
                domain = "TOTAL"
            for l, b in izip(data[::2], data[1::2]):
                l = l.lower()
                if l.startswith("xx-"):
                    l = "xx"
                if valid_languages and l not in valid_languages:
                    continue
                stats[domain][l] += int(b)

    for domain in stats:
        if args.nomono and len(stats[domain]) == 1:
            continue
        e = entropy(stats[domain])
        if args.total:
            crawl = args.infiles[0].name.split('.')[0]
            sys.stdout.write("%s\t%s\n" % (crawl, crawl))
            for language in sorted(stats[domain].keys()):
                sys.stdout.write(
                    "%s\t%d\n" % (language, stats[domain][language]))
        else:
            sys.stdout.write("%f %s" % (e, domain))
            for language in stats[domain]:
                sys.stdout.write(
                    " %s %d" % (language, stats[domain][language]))
            sys.stdout.write("\n")

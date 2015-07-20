#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from collections import defaultdict
from math import log

""" join language stat files together, possibly
    filering by langauge 

    input data are several file of format

    entropy domain l1 b1 [l2 b2 [l3 b3 [...]]]
    where
    * ln is a language identifier and
    * bn is the number of byes in that language

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
    parser.add_argument('infile', nargs='+', help="statistics files")
    parser.add_argument('-lang', nargs='*',
                        help="Ignore all other languages but these.")
    args = parser.parse_args()

    valid_languages = []
    if args.lang:
        valid_languages = [l.lower() for l in args.lang]

    stats = defaultdict(lambda: defaultdict(int))

    for filename in args.infile:
        for line in open(filename):
            _entropy, domain, data = line.split(' ', 2)
            data = data.split()
            for l, b in zip(data[::2], data[1::2]):
                stats[domain][l] += int(b)

    for domain in stats:
        e = entropy(stats[domain])
        sys.stdout.write("%f %s" % (e, domain))
        for language in stats[domain]:
            sys.stdout.write(" %s %d" % (language, stats[domain][language]))
        sys.stdout.write("\n")

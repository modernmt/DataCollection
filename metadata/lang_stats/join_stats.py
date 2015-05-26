#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from collections import defaultdict
from math import log


def entropy(lang_dist):
    total = float(sum(lang_dist.values()))
    h = 0

    if total == 0:
        sys.stderr.write("weird values: total: %f\n" % total)
        return h

    for lang, count in lang_dist.iteritems():
        p = float(count) / total
        try:
            h += p * log(p)
        except ValueError:
            sys.stderr.write("weird values: cnt: %d, total: %f\n"
                             % (count, total))
    return h


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('infile', nargs='?', type=argparse.FileType('r'))
    parser.add_argument('-lang', nargs='*',
                        help="Ignore all other languages but these.")
    args = parser.parse_args()

    valid_languages = []
    if args.lang:
        valid_languages = [l.lower() for l in args.lang]

    stats = defaultdict(lambda: defaultdict(int))

    for line in sys.stdin:
        domain, data = line.split(" ", 1)
        data = data.split()
        for language, num_bytes in zip(data[::2], data[1::2]):
            if valid_languages and language.lower() not in valid_languages:
                continue

            num_bytes = int(num_bytes)
            stats[domain][language] += num_bytes

    for domain in stats:
        e = entropy(stats[domain])
        sys.stdout.write("%f %s" % (e, domain))
        for language in stats[domain]:
            sys.stdout.write(" %s %d" % (language, stats[domain][language]))
        sys.stdout.write("\n")

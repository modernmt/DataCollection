#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from collections import defaultdict
from math import log

""" Collect language distribution per domain
    from language splitting output """


def netloc(url):
    # slightly faster than the urlparse version
    netloc = url.split('//', 1)[1].split('/', 1)[0]
    netloc = netloc.split(':', 1)[0].split('@')[-1]
    # netloc = urlparse(uri).netloc
    return netloc


def parse_line(line):
    data = {}
    for item in line.rstrip().split()[1:]:
        key, value = item.split(':', 1)
        if key == "bytes":
            value = int(value)
        data[key] = value
    return data


def entropy(lang_dist):
    total = float(sum(lang_dist.values()))
    h = 0
    for lang, count in lang_dist.iteritems():
        p = count / total
        h += p * log(p)
    return h

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-minbytes', type=int, default=100,
                        help="ignore chunks smaller than this.")
    parser.add_argument('-lang', nargs='*',
                        help="Ignore all other languages but these.")
    args = parser.parse_args(sys.argv[1:])

    stats = defaultdict(lambda: defaultdict(int))

    header = None
    full_domain = None
    valid_languages = []
    if args.lang:
        valid_languages = [l.lower() for l in args.lang]

    for linenr, line in enumerate(sys.stdin):
        header = parse_line(line)

        lang = header["language"]
        if valid_languages and lang.lower() not in valid_languages:
            continue

        if header["bytes"] >= args.minbytes:
            hostname = netloc(header["uri"])
            stats[hostname][lang] += header["bytes"]

for domain in stats:
    h = entropy(stats[domain])
    if h == 0.0:
        continue
    sys.stdout.write("%f %s" % (h, domain))
    counts = [(count, language)
              for language, count in stats[domain].iteritems()]
    counts.sort(reverse=True)
    for count, lang in counts:
        sys.stdout.write(" %s %d" % (lang, count))
    sys.stdout.write("\n")

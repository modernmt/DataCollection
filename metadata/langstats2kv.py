#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from collections import defaultdict
from metadatabase import make_key
import json

magic_number = 'df6fa1abb58549287111ba8d776733e9'


def parse_line(line):
    """ Example input:
    df6fa1abb58549287111ba8d776733e9 uri:http://0d1.info/ language:en offset:451 bytes:2743
    """
    d = {}
    for elem in line.rstrip().split()[1:]:
        k, v = elem.split(':', 1)
        d[k] = v
    return d


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('crawl', help='crawl format YYYY_WW, e.g. 2015_22')
    args = parser.parse_args(sys.argv[1:])

    stats = defaultdict(int)
    url = None

    for linenr, line in enumerate(sys.stdin):
        if not line.startswith(magic_number):
            continue
        line = parse_line(line)
        if url is not None and line['uri'] != url:
            sys.stdout.write("%s\t%s\n" % (
                make_key(url, args.crawl),
                json.dumps({"languages": stats.items()})))
            stats = defaultdict(int)
        url = line['uri']
        stats[line['language']] += int(line['bytes'])

    if url is not None:
        sys.stdout.write("%s\t%s\n" % (
            make_key(url, args.crawl),
            json.dumps({"languages": stats.items()})))

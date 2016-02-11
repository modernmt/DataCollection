#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys


def read_pairs(infile):
    pairs = []
    for line in infile:
        source_url, target_url = line.strip().split("\t")
        pairs.append((source_url, target_url))
    pairs = map(tuple, pairs)
    return pairs


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('devset',
                        help='correct pairs in dev set',
                        type=argparse.FileType('r'))

    args = parser.parse_args(sys.argv[1:])

    dev = set(read_pairs(args.devset))

    en, fr = set(), set()
    for line in sys.stdin:
        line = line.strip().split("\t")
        if not len(line) == 2:
            print "ERR:", line
            continue
        lang, url = line
        if lang == "en":
            en.add(url)
        else:
            assert lang == "fr"
            fr.add(url)

    for source_url, target_url in dev:
        if source_url not in fr:
            print "%s not identified as French" % (source_url)
        if target_url not in en:
            print "%s not identified as French" % (target_url)

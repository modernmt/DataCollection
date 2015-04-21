#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys


def has_prefix(prefixes, s):
    "Returns true if s starts with one of the prefixes"
    for p in prefixes:
        if s.startswith(p):
            return True
    return False

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--valid', type=argparse.FileType(),
                        help='file containing valid features, one per line')
    parser.add_argument('--prefix', nargs='+',
                        help='list of valid prefixes')
    args = parser.parse_args(sys.argv[1:])

    valid = set([l.strip() for l in args.valid]) if args.valid else set()

    for line in sys.stdin:
        label, feats = line.split("\t", 1)
        feats = [f for f in feats.strip().split() if
                 (valid and f in valid) or
                 (args.prefix and has_prefix(args.prefix, f))]
        sys.stdout.write("%s\t%s\n" % (label, " ".join(feats)))

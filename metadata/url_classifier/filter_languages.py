#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--valid', type=argparse.FileType(),
                        help='file containing valid label, one per line')
    parser.add_argument('--default',
                        help='replacement for invalid labels')
    args = parser.parse_args(sys.argv[1:])

    valid = set([l.strip() for l in args.valid])

    for line in sys.stdin:
        label, feats = line.split("\t", 1)
        if label not in valid:
            label = args.default
        if label:
            sys.stdout.write("%s\t%s" % (label, feats))

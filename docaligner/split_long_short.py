#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from itertools import izip

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=argparse.FileType('r'),
                        help='source corpus used to compute length')
    parser.add_argument('target', type=argparse.FileType('r'),
                        help='target corpus used to compute length')
    parser.add_argument('source_original', type=argparse.FileType('r'),
                        help='source corpus for output')
    parser.add_argument('target_original', type=argparse.FileType('r'),
                        help='target corpus for output')
    parser.add_argument('source_short', type=argparse.FileType('w'),
                        help='source corpus output file')
    parser.add_argument('target_short', type=argparse.FileType('w'),
                        help='target corpus output file')
    parser.add_argument('source_long', type=argparse.FileType('w'),
                        help='source corpus output file')
    parser.add_argument('target_long', type=argparse.FileType('w'),
                        help='target corpus output file')
    parser.add_argument('-n', type=int, default=50,
                        help='max tokens per line')
    args = parser.parse_args(sys.argv[1:])

    for sl, tl, s, t in izip(args.source, args.target,
                             args.source_original, args.target_original):
        if len(sl.split()) > args.n or len(tl.split()) > args.n:
            args.target_long.write(t)
            args.source_long.write(s)
        else:
            args.target_short.write(t)
            args.source_short.write(s)

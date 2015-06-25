#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
# ngrams = defaultdict(lambda: defaultdict:)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', type=int, default=4)
    args = parser.parse_args(sys.argv[1:])

    for line in sys.stdin:
        filename, text = line.split("\t", 1)
        text = text.strip().split()
        for start in range(len(text) - args.n + 1):
            sys.stdout.write(
                "%s\t%s\n" % (" ".join(text[start:start + args.n]), filename))

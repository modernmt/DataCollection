#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-devset', help='WMT16 devset',
                        type=argparse.FileType('r'))
    parser.add_argument('-file2url', help='mapping to real url',
                        type=argparse.FileType('r'))
    # parser.add_argument('bitextor', help='url to index mapping',
    #                     type=argparse.FileType('r'))

    args = parser.parse_args()

    mapping = {}
    for line in args.file2url:
        filename, url = line.strip().split('\t')
        mapping[filename] = url

    print "Read %d mappings" % len(mapping)

    bitextor_result = {}
    seen = set()
    for line in sys.stdin:
        line = line.strip().split('\t')
        e, f = line[:2]
        e = mapping.get(e, e)
        f = mapping.get(f, f)
        if f not in seen and e not in seen:
            seen.add(f)
            seen.add(e)
            bitextor_result[e] = f

    print "Total pairs: ", len(bitextor_result)

    devset = {}
    correct, wrong = [], []
    for line in args.devset:
        line = line.strip().split('\t')
        if len(line) > 2:
            line = line[1:4:2]  # indices 1 and 3
        f, e = line[:2]
        if bitextor_result.get(e, '') == f:
            correct.append(line)
        else:
            wrong.append(line)

    print "correct:", correct
    print "wrong:", wrong
    print len(correct), len(wrong)

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

    devset = set()
    seen = set()
    correct, wrong = [], []
    for line in args.devset:
        line = line.strip().split('\t')
        f, e = line[:2]

        if len(line) > 2:
            if line[0] == 'en' and line[2] == 'fr':
                e, f = line[1], line[3]
            elif line[0] == 'fr' and line[2] == 'en':
                f, e = line[1], line[3]

        if f not in seen and e not in seen:
            seen.add(f)
            seen.add(e)
            devset.add((f, e))
        elif (f, e) not in devset:
            print "already seen:"
            print f, e
            print devset
            sys.exit()

    for f, e in devset:
        if bitextor_result.get(e, '') == f:
            correct.append(line)
        else:
            wrong.append(line)

    # print "correct:", correct
    # print "wrong:", wrong
    print "correc, wrong, total"
    print len(correct), len(wrong), len(correct) + len(wrong)

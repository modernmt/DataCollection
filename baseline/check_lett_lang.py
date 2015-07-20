#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os

doc2lang = {}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('referencepairs', type=argparse.FileType('r'))
    parser.add_argument('-slang', help='Source language', default='en')
    parser.add_argument('-tlang', help='Non-english language', default='fr')
    parser.add_argument('-prefix', help='prefix added to make filenames',
                        default="/fs/syn0/pkoehn/crawl/data/site-crawls")

    args = parser.parse_args(sys.argv[1:])

    # read all the .lett files from stdin

    for line in sys.stdin:
        line = line.split("\t")
        if len(line) != 6:
            # sys.stderr.write("broken format: %s\n" % line[0])
            continue
        lang = line[0]
        filename = line[3].strip()
        if filename in doc2lang:
            sys.stderr.write("Duplicate entry: %s:%s\n" % (filename, lang))
        doc2lang[filename] = lang
        # print filename, lang

    correct = 0
    total = 0
    unknown = 0
    unknown_but_file = 0
    wrong_lang_pair = 0

    for line in args.referencepairs:
        total += 1
        domain, a, b = line.split("\t")
        a = a.strip()
        b = b.strip()

        found = True
        for f in (a, b):
            if f not in doc2lang:
                sys.stderr.write("unknown file %s\n" % (f))
                unknown += 1

                filename = os.path.join(args.prefix, f.split("/")[0], f)
                if os.path.isfile(filename):
                    sys.stderr.write("but file %s exists\n" % (filename))
                    unknown_but_file += 1

                found = False
            elif doc2lang[f] not in (args.slang, args.tlang):
                sys.stderr.write("%s detected as neither %s or %s\n"
                                 % (f, args.slang, args.tland))
                wrong_lang_pair += 1
                found = False

        if not found:
            continue

        if doc2lang[a] == doc2lang[b]:
            sys.stderr.write("Found both %s and %s to be in %s\n"
                             % (a, b, doc2lang[b]))
            wrong_lang_pair += 1
            continue

        correct += 1

    print "Total: ", total
    print "Possible: ", correct
    print "Unknown: ", unknown
    print "Unknown but file exists: ", unknown_but_file
    print "Wrong_lang_pair: ", wrong_lang_pair

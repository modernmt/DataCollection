#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import sys
import langid
from collections import defaultdict


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('infile', nargs='?', type=argparse.FileType('r'),
                        default=sys.stdin)
    parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'),
                        default=sys.stdout)
    parser.add_argument('-s', '--lang1', help='source language',
                        dest='source_lang', default='en')
    parser.add_argument('-t', '--lang2', help='target language',
                        dest='target_lang', default='fr')
    args = parser.parse_args()

    deletions = defaultdict(list)

    endCount = 0
    totalCount = 0
    langid.set_languages([args.source_lang, args.target_lang])
    for line in args.infile:
        totalCount += 1
        [url1, url2, source, target, score] = line.split("\t")
        langid_source = langid.classify(source.lower())
        langid_target = langid.classify(target.lower())
        if not source.strip():
            deletions["source_empty"].append(source)
        elif not target.strip():
            deletions["target_empty"].append(target)
        elif langid_source[0] != args.source_lang and langid_source[1] > 0.9:
            deletions["source_lang"].append(
                "%s\t%s\t%f" % (source, langid_source[0], langid_source[1]))
        elif langid_target[0] != args.target_lang and langid_target[1] > 0.9:
            deletions["target_lang"].append(
                "%s\t%s\t%f" % (target, langid_target[0], langid_target[1]))
        elif source == target:
            deletions["identical"].append(target)
        elif float((len(source) + 15)) / float(len(target) + 15) > 1.5:
            deletions["source_too_long"].append("%s\t%s" % (source, target))
        elif float((len(target) + 15)) / float(len(source) + 15) > 1.5:
            deletions["source_too_short"].append("%s\t%s" % (source, target))
        else:
            args.outfile.write(line)
            endCount += 1
    print "Written: %d of %d = %f percent" % (endCount, totalCount,
                                              100. * endCount / totalCount)
    for reason, deleted in deletions.iteritems():
        print "Deleted %d items due to %s" % (len(deleted), reason)
        for line in deleted:
            print "\t%s" % line

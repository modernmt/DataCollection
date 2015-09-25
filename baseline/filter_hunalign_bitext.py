#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import sys
import langid
from collections import defaultdict

""" Removes some wrongly aligned pairs from hunalign output """


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('infile', nargs='?', type=argparse.FileType('r'),
                        default=sys.stdin)
    parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'),
                        default=sys.stdout)
    parser.add_argument('-minscore', type=float, default=0,
                        help='minimum score from hunalign')
    parser.add_argument('-s', '--lang1', help='source language',
                        dest='source_lang', default='en')
    parser.add_argument('-t', '--lang2', help='target language',
                        dest='target_lang', default='fr')
    args = parser.parse_args()

    deletions = defaultdict(list)

    n_written = 0
    n_total = 0
    langid.set_languages([args.source_lang, args.target_lang])
    for line in args.infile:
        n_total += 1
        source, target, score = line.split("\t")
        source = source.decode('utf-8', 'ignore')
        target = target.decode('utf-8', 'ignore')
        if float(score) < args.minscore:
            deletions["low score"].append('')
            continue
        if source == target:
            deletions["identical"].append(target)
            continue
        if not source.strip():
            deletions["source_empty"].append('')
            continue
        elif not target.strip():
            deletions["target_empty"].append('')
            continue

        langid_source = langid.classify(source.lower())
        if langid_source[0] != args.source_lang and langid_source[1] > 0.9:
            deletions["source_lang"].append(
                "%s\t%s\t%f" % (source, langid_source[0], langid_source[1]))
            continue
        langid_target = langid.classify(target.lower())
        if langid_target[0] != args.target_lang and langid_target[1] > 0.9:
            deletions["target_lang"].append(
                "%s\t%s\t%f" % (target, langid_target[0], langid_target[1]))
            continue

        # source = source.decode('utf-8', 'ignore')
        # target = target.decode('utf-8', 'ignore')
        if float((len(source) + 15)) / float(len(target) + 15) > 1.5:
            deletions["source_too_long"].append("%s\t%s" % (source, target))
        elif float((len(target) + 15)) / float(len(source) + 15) > 1.5:
            deletions["source_too_short"].append("%s\t%s" % (source, target))
        else:
            args.outfile.write(line)
            n_written += 1
    print "Written: %d of %d = %f percent" % (n_written, n_total,
                                              100. * n_written / n_total)
    for reason, deleted in deletions.iteritems():
        print "Deleted %d items due to %s" % (len(deleted), reason)
        for line in deleted:
            if line.strip():
                print "\t%s" % line.encode('utf-8')

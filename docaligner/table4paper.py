#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from lett import read_lett
import locale
locale.setlocale(locale.LC_ALL, '')


def read_devset(fh):
    # format fr-url <TAB> en-url
    surls, turls = set(), set()
    # print "Reading devset from ", fh.name
    for line in fh:
        surl, turl = line.strip().split('\t')
        surls.add(surl)
        turls.add(turl)

    assert len(surls) == len(turls)
    return surls, turls


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'devset', help='correct pairs', type=argparse.FileType('r'))
    parser.add_argument(
        'lettfile', help='input lett file', type=argparse.FileType('r'))
    parser.add_argument('-slang', help='source language', default='en')
    parser.add_argument('-tlang', help='target language', default='fr')
    args = parser.parse_args()

    surls, turls = read_devset(args.devset)
    sys.stderr.write("Read %d devpairs\n" % (len(surls)))

    # read source and target corpus
    s, t = read_lett(args.lettfile, args.slang, args.tlang)

    source_found = 0
    for url, page in s.iteritems():
        if page.url in surls:
            source_found += 1

    target_found = 0
    for url, page in t.iteritems():
        if page.url in turls:
            target_found += 1

    assert source_found == target_found

    name = args.lettfile.name.replace('.lett.gz', '')
    n_source = locale.format("%d", len(s), grouping=True)
    n_target = locale.format("%d", len(t), grouping=True)
    n_pairs = locale.format("%d", len(s) * len(t), grouping=True)
    source_found = locale.format("%d", source_found, grouping=True)
    target_found = locale.format("%d", target_found, grouping=True)
    # forcesavenir.qc &   3,592   &   3,982   &   14,303,344  &   8 \\
    sys.stdout.write("%s &\t %s &\t %s &\t %s &\t %s \\\\\n"
                     % (name, n_source, n_target, n_pairs, source_found))

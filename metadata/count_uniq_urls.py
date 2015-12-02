#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import hyperloglog
import gzip
from subprocess import Popen, PIPE

""" Estimates the approximate number of unique urls in .kv files """


def read_urls(f):
    """ Reads from filehandle and produces the 2nd column """
    for linenr, line in enumerate(f):
        _, url, _ = line.split(' ', 2)
        yield url


def combinations(l):
    """ Produces all combinations of values from l """
    for i, a in enumerate(l):
        for b in l[i + 1:]:
            yield a, b


def open_file(fname):
    # print "opening %s" % str(fname)
    if fname.endswith('gz'):
        f = Popen(['zcat', fname], stdout=PIPE, stderr=PIPE)
        return f.stdout
        # return gzip.open(fname)
    else:
        return open(fname)


def incremental_stats(fnames, err):
    hll = hyperloglog.HyperLogLog(err)  # 0.1 = 10% error
    for fname in fnames:
        n_lines = 0
        hll_local = hyperloglog.HyperLogLog(err)
        for url in read_urls(open_file(fname)):
            n_lines += 1
            hll_local.add(url)
            hll.add(url)
        print "%s\t%d\t%d\t%d" % (fname, n_lines, len(hll_local), len(hll))


def combination_stats(fnames, err):
    for fn1, fn2 in combinations(fnames):
        incremental_stats((fn1, fn2), err)
        print "--"


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('files', help='kv files', nargs='+')
    parser.add_argument('-incremental', help='produce incremental statistics',
                        action='store_true')
    parser.add_argument('-error', help='counting error, default: .1%',
                        type=float, default=0.001)
    args = parser.parse_args(sys.argv[1:])

    if args.incremental:
        incremental_stats(args.files, args.error)
    else:
        combination_stats(args.files, args.error)

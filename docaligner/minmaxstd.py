#!/usr/bin/env python
# -*- coding: utf-8 -*-
import numpy as np
import sys
import gzip

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('infile', help='input text format matrix')
    parser.add_argument('-outfile', help='output npz file')
    args = parser.parse_args(sys.argv[1:])

    fh = open(args.infile, 'r')
    if args.infile.endswith('.gz'):
        fh = gzip.open(args.infile)
    m = np.load(fh)

    print "Loaded ", args.infile, " of shape ", m.shape
    print "Std\t", np.std(m)
    print "Min\t", np.min(m)
    print "Max\t", np.max(m)
    print "Mean\t", np.average(m)
    print "Median\t", np.median(m)

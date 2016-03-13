#!/usr/bin/env python
# -*- coding: utf-8 -*-
import numpy as np
import sys

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('infile', help='input text format matrix')
    parser.add_argument('-outfile', help='output npz file')
    args = parser.parse_args(sys.argv[1:])

    if args.infile.endswith('npz'):
        m = np.load(args.infile)['m']
    else:
        m = np.loadtxt(args.infile)
    print "Loaded ", args.infile, " of shape ", m.shape
    if args.outfile:
        np.save(args.outfile, m)
    print "Wrote ", args.outfile, " of shape ", m.shape

#!/bin/bash
# -*- coding: utf-8 -*-

"""
Extract original URL from httrack webdir
"""

import sys
import re

# Example line we're looking for:
# <!-- Mirrored from www.tekstwerk.com/en by HTTrack ...


magic_number = "df6fa1abb58549287111ba8d776733e9"

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('infile', help='name of file in httrack webdir',
                        nargs='+')
    # parser.add_argument('outfile', type=argparse.FileType('w'),
    #                     help='output file')
    args = parser.parse_args(sys.argv[1:])

    for filename in args.infile:
        html = open(filename, 'r').read()
        m = re.search("<!-- Mirrored from (\S+) by HTTrack", html)
        if m:
            url = m.groups()[0]
            sys.stdout.write("%s\t%s\n" % (filename, url))
        else:
            sys.stderr.write("No URL found for %s\n" % filename)

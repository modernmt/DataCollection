#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Reads downloaded website from tar file and writes lett format to be
processed by bitextor pipeline
"""

import sys
import tarfile
from util import encoding


magic_number = "df6fa1abb58549287111ba8d776733e9"

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('tarfile', help='tarfile containing a webdir')
    parser.add_argument('outfile', type=argparse.FileType('w'),
                        help='output file')
    args = parser.parse_args(sys.argv[1:])

    tar = tarfile.open(args.tarfile, "r:gz")

    for tarinfo in tar:
        if not tarinfo.isreg():
            continue
        data = tar.extractfile(tarinfo).read()
        data = encoding.convert_to_utf8(data)
        args.outfile.write("%s uri:%s\n" % (magic_number, tarinfo.name))
        args.outfile.write(data.encode("utf-8"))
        args.outfile.write("\n")
    tar.close()

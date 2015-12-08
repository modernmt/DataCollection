#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Reads downloaded website from tar file and writes lett format to be
processed by bitextor pipeline
"""

import sys
import tarfile
from textsanitzer import TextSanitizer


magic_number = "df6fa1abb58549287111ba8d776733e9"


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('tarfile', help='tarfile containing a webdir')
    parser.add_argument('outfile', type=argparse.FileType('w'),
                        help='output file')
    parser.add_argument('-unicode', action='store_true',
                        help='ensure unicode output')
    parser.add_argument('-language',
                        help='possible language for encoding guessing')
    args = parser.parse_args(sys.argv[1:])

    tar = tarfile.open(args.tarfile, "r:gz")

    for tarinfo in tar:
        if not tarinfo.isreg():
            continue
        data = tar.extractfile(tarinfo).read()
        args.outfile.write("%s uri:%s\n" % (magic_number, tarinfo.name))
        if args.unicode:
            data = TextSanitizer.to_unicode(
                data, is_html=True, lang=args.language)
            args.outfile.write(data.encode("utf-8"))
        else:
            args.outfile.write(data)
        args.outfile.write("\n")
    tar.close()

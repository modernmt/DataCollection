#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Reads downloaded website from tar file and writes lett format to be
processed by bitextor pipeline
"""

import sys
import tarfile
from util import encoding
from html2text import html2text
#from base64 import base64
import base64

magic_number = "df6fa1abb58549287111ba8d776733e9"


name2code = {"ENGLISH": "en", "FRENCH": "fr"}


def read_statsfile(f):
    stats = {}
    url, length = None, None
    for line in f:
        if line.startswith(magic_number):
            n, url, length = line.split(' ', 2)
            url = url.split(":")[1]
            length = int(length.split(':')[1])
        else:
            assert url is not None
            assert length is not None
            if url in stats:
                # ignore all but first entry
                continue
            else:
                lang = line.split()[0]
                if lang == "Unknown":
                    continue
                if lang not in name2code:
                    sys.stderr.write("Unexpected language: %s\n" % lang)
                    continue
                stats[url] = name2code[lang]
    return stats

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('tarfile', help='tarfile containing a webdir')
    parser.add_argument(
        'statsfile', help='language statistics', type=argparse.FileType('r'))
    parser.add_argument('srclang', help="source langauge e.g. en")
    parser.add_argument('tgtlang', help="target langauge e.g. fr")
    parser.add_argument('lett', type=argparse.FileType('w'),
                        help='output lett file')
    parser.add_argument('-ignore_br', help="ignore <br> tags in HTML",
                        action='store_true', default=False)

    mime_type = "text/html"
    enc = "charset=utf-8"

    args = parser.parse_args(sys.argv[1:])
    lang_stats = read_statsfile(args.statsfile)

    tar = tarfile.open(args.tarfile, "r:gz")

    for tarinfo in tar:
        if not tarinfo.isreg():
            continue
        data = tar.extractfile(tarinfo).read()
        data = encoding.convert_to_utf8(data)
        text = html2text(data.encode("utf-8"),  # utf-8 input expected
                         sanitize=True,
                         ignore_br=args.ignore_br)
        uri = tarinfo.name
        if uri not in lang_stats:
            sys.stderr.write("No langstats for file %s\n" % uri)
        if uri not in lang_stats:
            continue
        lang = lang_stats[uri]

        args.lett.write("{l}\t{mime}\t{enc}\t{name}\t{html}\t{text}\n".format(
            l=lang,
            mime=mime_type,
            enc=enc,
            name=uri,
            html=base64.b64encode(data.encode("utf-8")),
            text=base64.b64encode(text.encode("utf-8"))))

        # args.outfile.write("%s uri:%s\n" % (magic_number, tarinfo.name))
        # args.outfile.write(data.encode("utf-8"))
    tar.close()

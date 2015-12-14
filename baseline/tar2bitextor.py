#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Reads downloaded website from tar file and writes lett format to be
processed by bitextor pipeline
"""

import sys
import tarfile
import base64
import re

from html2text import html2text
from textsanitzer import TextSanitizer

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


def original_url(html):
    """ Extracts the original url from HTTrack comment """
    m = re.search(r"<!-- Mirrored from ([^>]+) by HTTrack Website Copier",
                  html)
    if m is None:
        return "unknown_url"
    return m.groups()[0]


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('tarfile', help='tarfile containing a webdir')
    parser.add_argument('srclang', help="source langauge e.g. en")
    parser.add_argument('tgtlang', help="target langauge e.g. fr")
    parser.add_argument('lett', type=argparse.FileType('w'),
                        help='output lett file')
    parser.add_argument('-ignore_br', help="ignore <br> tags in HTML",
                        action='store_true', default=False)
    parser.add_argument('-filter-other-languages',
                        dest='filter',
                        help='remove pages in other languages',
                        action='store_true')

    mime_type = "text/html"
    enc = "charset=utf-8"

    args = parser.parse_args(sys.argv[1:])
    tar = tarfile.open(args.tarfile, "r:gz")

    for filenr, tarinfo in enumerate(tar):
        if not tarinfo.isreg():
            continue

        filename = tarinfo.name

        raw_data = tar.extractfile(tarinfo).read()
        data = TextSanitizer.to_unicode(raw_data, is_html=True, lang='auto')
        lang = TextSanitizer.guess_lang_from_data(
            data, is_html=True, default_lang=None)

        if not lang:
            sys.stderr.write("No langs for file %s\n" % filename)
            continue
        if args.filter and lang != args.srclang and lang != args.tgtlang:
            sys.stderr.write("Skipping %s because lang=%s\n" %
                             (filename, lang))
            continue

        text = html2text(data.encode('utf-8'),  # utf-8 input expected
                         sanitize=True,
                         ignore_br=args.ignore_br)

        original_uri = original_url(data)

        sys.stderr.write("Processed file Nr. %d : %s = %s\n" %
                         (filenr, filename, original_uri.encode('utf-8')))

        args.lett.write("{l}\t{mime}\t{enc}\t{name}\t{html}\t{text}\n".format(
            l=lang,
            mime=mime_type,
            enc=enc,
            name=original_uri.encode('utf-8'),
            html=base64.b64encode(data.encode('utf-8')),
            text=base64.b64encode(text.encode('utf-8'))))

    tar.close()

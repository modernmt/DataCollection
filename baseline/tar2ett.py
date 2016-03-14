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


def original_url_from_httrack_comment(html):
    """ Extracts the original url from HTTrack comment """
    url = "unknown_url"
    for m in re.finditer(
            "<!-- Mirrored from ([^>]+) by HTTrack Website Copier", html):
        url = m.groups()[0]
        if not url.startswith('http://'):
            url = "http://" + url
    return url


def read_file2realurl(fh):
    file2realurl = {}
    if fh:
        for line in fh:
            filename, real_url = line.strip().split("\t")
            assert filename not in file2realurl
            file2realurl[filename] = real_url
    return file2realurl

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('tarfile', help='tarfile containing a webdir')
    # parser.add_argument('srclang', help="source langauge e.g. en")
    # parser.add_argument('tgtlang', help="target langauge e.g. fr")
    # parser.add_argument('-out', type=argparse.FileType('w'),
    #                     help='output lett file',
    #                     default=sys.stdout)
    parser.add_argument('-out', type=argparse.FileType('w'),
                        help='output lett file',
                        default=sys.stdout)
    parser.add_argument('-file2url', type=argparse.FileType('w'),
                        help='filename to URL mapping')

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
        data = data.encode('utf-8')  # utf-8 input expected

        original_uri = original_url_from_httrack_comment(data)
        if args.file2url:
            args.file2url.write("%s\t%s\n" % (original_uri, filename))
        if original_uri == "unknown_url":
            original_uri = filename

        sys.stderr.write("Processed file Nr. %d : %s = %s\n" %
                         (filenr, filename, original_uri))

        links = re.findall('''href\s*=\s*['"]\s*([^'"]+)['"]''', data, re.S)
        sys.stdout.write("{html}\t{url}\t{links}\n".format(
            html=base64.b64encode(data),
            url=original_uri,
            links=str(list(set(links)))))

    sys.stderr.write("Done. \n")
    tar.close()

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from strip_language_from_uri import LanguageStripper
from collections import defaultdict
import urlparse

""" produces the .ridx file from a lett file by ignoring content in
    favour of url matching
"""


def strip_uri(uri, language_stripper):
    parsed_uri = urlparse.urlparse(uri)

    matched_language = language_stripper.match(parsed_uri.path)
    if not matched_language:
        matched_language = language_stripper.match(parsed_uri.query)
        assert matched_language, repr(parsed_uri)

    stripped_path = language_stripper.strip(parsed_uri.path)
    stripped_query = language_stripper.strip(parsed_uri.query)
    stripped_uri = urlparse.ParseResult(parsed_uri.scheme,
                                        parsed_uri.netloc,
                                        stripped_path,
                                        parsed_uri.params,
                                        stripped_query,
                                        parsed_uri.fragment).geturl()
    return matched_language, stripped_uri

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        'infile', type=argparse.FileType('r'), default=sys.stdin)
    parser.add_argument(
        'outfile', type=argparse.FileType('w'), default=sys.stdout)
    args = parser.parse_args()
    stripper = LanguageStripper()

    urls_src = []
    urls_tgt = defaultdict(list)
    for linenr, line in enumerate(args.infile):
        line = line.split("\t")
        url = line[3]
        lang, stripped_url = strip_uri(url, stripper)
        if lang == "ENGLISH":
            urls_src.append((linenr, stripped_url))
            continue
        else:
            assert lang == "FRENCH", "L: %s url: %s \n" % (lang, url)
            urls_tgt[stripped_url].append(linenr)

    for linenr, stripped_url in urls_src:
        # source lang urls appear first in the file
        assert stripped_url in urls_tgt, "URL not fould: %s (%s)" % (
            stripped_url, url)
        args.outfile.write("%d" % (linenr + 1))
        for i in urls_tgt[stripped_url]:
            args.outfile.write("\t%d:1.0" % (i + 1))
        args.outfile.write("\n")

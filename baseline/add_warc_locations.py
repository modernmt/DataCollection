#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import gzip
import json
from urlparse import urlparse
import tldextract

# Input looks like this:
# lang-independent url    url                       ELANG   LANGS
# where ELANG is the expected language, based on what was removed from the url
# and LANGS are the languages that were detected in the page
# Example:
# http://15october.net//  http://15october.net/ar/  ARABIC  ARABIC/ENGLISH
# http://15october.net//  http://15october.net/de/  GERMAN  GERMAN/ENGLISH
# http://15october.net//  http://15october.net/es/  SPANISH SPANISH/ENGLISH
# http://15october.net//  http://15october.net/es/  SPANISH SPANISH/ENGLISH
# http://15october.net//  http://15october.net/fr/  FRENCH  FRENCH/ENGLISH


def get_tld(uri):
    tld = tldextract.extract(urlparse(uri).netloc)
    return tld


def read_candidates(candidates):
    valid_tlds = set()
    uri_dict = {}
    for line in args.candidates:
        line = line.strip().split("\t")
        assert len(line) == 4, "weird line: %s\n" % "\t".join(line)
        uri = line[1]
        tld = get_tld(uri).domain
        # print uri, tld
        valid_tlds.add(tld)
        uri_dict[uri] = "\t".join(line)

    return valid_tlds, uri_dict


def open_file(filename):
    if filename.lower().endswith(".gz"):
        return gzip.open(filename)
    return open(filename)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('candidates', type=open_file,
                        help='file containing candidates')
    parser.add_argument('--prefix', help='prefix for filename',
                        default='')

    parser.add_argument('--outfile', type=argparse.FileType('w'),
                        default=sys.stdout)
    args = parser.parse_args(sys.argv[1:])

    valid_tlds, uri_dict = read_candidates(args.candidates)
    sys.stderr.write("Looking for %d URLs from %d domains\n" %
                     (len(uri_dict), len(valid_tlds)))

    tld_found, uri_found, n_lines, errors = 0, 0, 0, 0
    for line in sys.stdin:
        tld, json_data = line.split(" ", 1)
        n_lines += 1
        if tld not in valid_tlds:
            continue

        tld_found += 1

        data = json.loads(json_data)
        if data["uri"] not in uri_dict:
            continue
        uri_found += 1
        try:
            container_data = data["container"]
            offset = container_data["Offset"]
            length = container_data["Gzip-Metadata"]["Deflate-Length"]
            filename = args.prefix + container_data["Filename"]
            original = uri_dict[data["uri"]]
            sys.stdout.write("%s\t%s\t%d\t%d\n" %
                             (original, filename, int(offset), int(length)))
        except KeyError:
            errors += 1

    sys.stderr.write("Found %d tld and %d uris in %d lines (%d errors)\n"
                     % (tld_found, uri_found, n_lines, errors))

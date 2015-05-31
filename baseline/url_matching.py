#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import os
from strip_language_from_uri import LanguageStripper
import chardet
from collections import defaultdict
import re
import urlparse


def has_prefix(prefixes, s):
    "Returns true if s starts with one of the prefixes"
    for p in prefixes:
        if s.startswith(p):
            return True
    return False


def original_url(html):
    m = re.search(r"<!-- Mirrored from ([^>]+) by HTTrack Website Copier",
                  html)
    if m is None:
        return "unknown_url"
    return m.groups()[0]


def clean_whitespace(s):
    # remove empty lines
    s = [l.strip() for l in s.split("\n") if l.strip()]
    return "\n".join(re.sub("\s+", " ", l) for l in s)


def read_file(filename):
    # sys.stderr.write("reading: %s\n" % filename)
    f = open(filename, 'r')
    html = f.read()
    try:
        html = html.decode("utf-8")
    except:
        encoding = chardet.detect(html)
        try:
            html = html.decode(encoding["encoding"])
        except:
            sys.stderr.write(
                "Fallback: ignoring errors for file%s\n" % filename)
            return html.decode("utf-8", errors='ignore')
    return html


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('outfile', type=argparse.FileType('w'),
                        help='output file')
    parser.add_argument('-prefix', help='prefix added to make filenames',
                        default="/fs/syn0/pkoehn/crawl/data/site-crawls")
    parser.add_argument('-slang', help='source language', default='en')
    parser.add_argument('-tlang', help='target language', default='fr')
    args = parser.parse_args(sys.argv[1:])

    correct = 0
    stripper = LanguageStripper()
    for line in sys.stdin:
        was_stripped = 0
        domain, a, b = line.strip().split("\t")

        urls = defaultdict(list)
        for s in (a, b):
            filename = os.path.join(args.prefix, domain, s)
            html = read_file(filename)

            url = original_url(html)
            url = "http://" + url
            # print url

            parsed_url = urlparse.urlparse(url)
            stripped_path = stripper.strip(parsed_url.path).replace("//", "/")
            stripped_query = stripper.strip(
                parsed_url.query).replace("//", "/")
            stripped_url = urlparse.ParseResult(parsed_url.scheme,
                                                parsed_url.netloc,
                                                stripped_path,
                                                parsed_url.params,
                                                stripped_query,
                                                parsed_url.fragment).geturl()

            urls[stripped_url].append(url)
            if stripped_url != url:
                was_stripped += 1
        if len(urls) == 1:
            correct += 1

        print len(urls), was_stripped, correct, urls.items()

    print "correct: ", correct

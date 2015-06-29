#!/usr/bin/env python
# -*- coding: utf-8 -*-
from collections import defaultdict
from urlparse import urlparse
import gzip
import os
import sys
import tldextract
from ccdownloader import CCDownloader


def get_domain(uri):
    extract = tldextract.extract(urlparse(uri).netloc)
    return ".".join((extract.domain.encode('idna'), extract.suffix))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('srclang', help="source langauge")
    parser.add_argument('tgtlang', help="target langauge")
    parser.add_argument('crawl', help='crawl id, e.g. 2013_11')
    parser.add_argument('--outdir', help='prefix for filenames',
                        default='data/')
    args = parser.parse_args(sys.argv[1:])

    source_lines, target_lines = defaultdict(list), defaultdict(list)
    for line in sys.stdin:
        line = line.strip().split()
        lang = line[2]
        language_independent_url = line[0]
        if lang == args.srclang:
            source_lines[language_independent_url].append(line)
        elif lang == args.tgtlang:
            target_lines[language_independent_url].append(line)
        else:
            continue

    downloader = CCDownloader()

    for language_independent_url in source_lines:
        if language_independent_url in target_lines:
            domain = get_domain(source_lines[language_independent_url][0][1])

            outfile = gzip.open(
                os.path.join(args.outdir,
                             "%s_%s.gz" % (domain, args.srclang)), "a", 9)
            for line in source_lines[language_independent_url]:
                downloader.download_and_write(line, outfile, args.crawl)
            outfile.close()

            outfile = gzip.open(
                os.path.join(args.outdir,
                             "%s_%s.gz" % (domain, args.tgtlang)), "a", 9)
            for line in target_lines[language_independent_url]:
                downloader.download_and_write(line, outfile, args.crawl)
            outfile.close()

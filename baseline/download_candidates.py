#!/usr/bin/env python
# -*- coding: utf-8 -*-
from collections import defaultdict
from urlparse import urlparse
import gzip
import os
import requests
import sys
import tldextract
import zlib

magic_number = "df6fa1abb58549287111ba8d776733e9"


class CCDownloader(object):

    def __init__(self):
        self.session = requests.Session()

    def make_full_path(self, crawl, folder, filename):
        return "https://aws-publicdatasets.s3.amazonaws.com/" +\
               "common-crawl/crawl-data/" + \
               "CC-MAIN-%s" % crawl.replace("_", "-") +\
               "/segments/%d" % (int(folder)) +\
               "/warc/%s" % filename.replace("warc.wat.gz", "warc.gz")

    def download(self, location, offset, length):
        start_range = offset
        end_range = offset + length - 1
        r = {'Range': "bytes=%d-%d" % (start_range, end_range)}
        try:
            resp = self.session.get(location, headers=r)
        except:
            self.session = requests.Session()
            return ""
        try:
            return zlib.decompress(resp.content, zlib.MAX_WBITS | 16)
        except:
            sys.stderr.write("Error decompressing %d bytes from %s: %d-%d\n"
                             % (len(resp.content),
                                location, start_range, end_range))
            return ""

    def extract_html(self, raw_page):
        empty_lines_seen = 0
        page = raw_page.split("\n")
        for linenr, line in enumerate(page):
            if not line.strip():
                empty_lines_seen += 1
                if empty_lines_seen == 2:
                    return "\n".join(page[linenr + 1:])
        raise ValueError("Input must contain two empty lines")

    def download_and_write(self, line, outfile, html_only=False):
        folder, filename = line[4].split('/')
        full_filename = self.make_full_path(args.crawl, folder, filename)
        offset = int(line[5])
        length = int(line[6])
        raw_page = self.download(full_filename, offset, length)
        sys.stderr.write("%s : %d bytes\n" % (line[1], len(raw_page)))
        if raw_page:
            outfile.write("%s\t%s\n" % (magic_number, "\t".join(line)))
            if html_only:
                outfile.write(self.extract_html(raw_page))
            else:
                outfile.write(raw_page)


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
                downloader.download_and_write(line, outfile)
            outfile.close()

            outfile = gzip.open(
                os.path.join(args.outdir,
                             "%s_%s.gz" % (domain, args.tgtlang)), "a", 9)
            for line in target_lines[language_independent_url]:
                downloader.download_and_write(line, outfile)
            outfile.close()

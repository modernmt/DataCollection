#!/usr/bin/env python
# -*- coding: utf-8 -*-
from urlparse import urlparse
import sys
import tldextract
import requests
from ccdownloader import CCDownloader


def get_domain(uri):
    extract = tldextract.extract(urlparse(uri).netloc)
    return ".".join((extract.domain.encode('idna'), extract.suffix))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('domain', help="domain to download")
    parser.add_argument('-api', default="http://statmt.org:8031/query_domain")
    parser.add_argument('-outfile', type=argparse.FileType('w'),
                        help='output file', default=sys.stdout)
    args = parser.parse_args(sys.argv[1:])

    downloader = CCDownloader()

    payload = {"url": args.domain, "max_results": 1000000, "full": 1}
    resp = requests.get(args.api, params=payload)

    data = resp.json()['data']
    downloaded_pages, downloaded_bytes = 0, 0.
    for url, crawldata in data.iteritems():
        for crawl, metadata in crawldata:
            if metadata.get('mime', "text/html") != "text/html":
                continue
            # work around stupid typo
            offset = metadata['offset'] \
                if 'offset' in metadata else metadata['offset:']
            raw_page = downloader.download(
                metadata['filename'], int(offset), int(metadata['length']))
            if not raw_page:
                continue

            header = "%s %s\n" % (CCDownloader.magic_number, url)
            args.outfile.write(header)
            args.outfile.write(raw_page)
            args.outfile.write("\n")
            downloaded_bytes += len(raw_page)
            downloaded_pages += 1

    sys.stderr.write("%s: downloaded %d spages, total of %0.3f Mbytes\n" % (
        args.domain, downloaded_pages, downloaded_bytes / 1024 / 1024))

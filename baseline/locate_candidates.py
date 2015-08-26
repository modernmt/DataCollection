#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import json
import tldextract
import re
import requests

 # curl -v "http://statmt.org:8030/query_domain?domain=caletas.cr&full"


def get_tld(uri):
    try:
        netloc = uri.split(
            '//', 1)[1].split('/', 1)[0].split(':', 1)[0].split('@')[-1]
    except IndexError:
        return ""
    # netloc = urlparse(uri)
    try:
        tld = tldextract.extract(netloc)
    except UnicodeError:
        return None
    except IndexError:
        return None
    return tld


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('candidates', type=argparse.FileType('r'),
                        help='file containing candidates')
    parser.add_argument('outfile', type=argparse.FileType('w'),
                        default=sys.stdout)
    parser.add_argument('-server', help='metadata server location',
                        default='http://localhost:8080/query_domain')
    parser.add_argument('-slang', help='source language (e.g. en)',
                        default='en')
    parser.add_argument('-tlang', help='source language (e.g. it)',
                        default='it')
    args = parser.parse_args(sys.argv[1:])

    n, errors = 0, 0
    for line in args.candidates:
        _, src_url, src_crawl, tgt_url, tgt_crawl = line.strip().split()
        n += 1

        for url, crawl, lang in ((src_url, src_crawl, args.slang),
                                 (tgt_url, tgt_crawl, args.tlang)):

            payload = {'domain': url, 'crawl': crawl, 'full': 1,
                       'max_results': 1}
            r = requests.get(args.server, params=payload)
            data = r.json()['data']
            if url not in data:
                payload['max_results'] = 1000
                r = requests.get(args.server, params=payload)
                data = r.json()['data']
                if url not in data:
                    errors += 1
                    print "Errors: %d/%d=%.2f\t%s %s" % (n, errors, 100. * n / errors, url, crawl)

        # sys.exit()

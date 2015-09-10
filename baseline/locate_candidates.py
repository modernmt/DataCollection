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


def get_location(session, url, crawl, server):
    """ Returns success and location """
    payload = {'url': url, 'crawl': crawl,
               'max_results': 1, 'verbose': 1, 'exact': 1}
    r = session.get(server, params=payload)
    assert 'locations' in r.json(), "line:%s\nquery: %s\nrespons:%s\n" % \
        (line,
         json.dumps(payload),
         json.dumps(r.json()))
    data = r.json()['locations']
    if url not in data:
        assert len(data) == 0
        return False, None
    return True, data[url][0]


def report_error(url, crawl, errors, total):
    percentage = 100. * errors / total
    sys.stderr.write("Errors: %d/%d = %.2f%%\t%s\t%s\n" %
                     (errors, total, percentage, crawl, url))


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('candidates', type=argparse.FileType('r'),
                        help='file containing candidates')
    parser.add_argument('outfile', type=argparse.FileType('w'),
                        default=sys.stdout)
    parser.add_argument('-server', help='metadata server location',
                        default='http://localhost:8080/query_prefix')
    parser.add_argument('-slang', help='source language (e.g. en)',
                        default='en')
    parser.add_argument('-tlang', help='source language (e.g. it)',
                        default='it')
    args = parser.parse_args(sys.argv[1:])

    total_lines, total_errors = 0, 0
    with requests.Session() as session:
        for line in args.candidates:
            total_lines += 1
            line = line.decode("utf-8")
            _, src_url, src_crawl, tgt_url, tgt_crawl = line.strip().split()

            src_success, src_loc = get_location(session, src_url,
                                                src_crawl, args.server)
            if not src_success:
                total_errors += 1
                report_error(src_url, src_crawl, total_errors, total_lines)

            tgt_success, tgt_loc = get_location(session, tgt_url,
                                                tgt_crawl, args.server)
            if not tgt_success:
                total_errors += 1
                report_error(tgt_url, tgt_crawl, total_errors, total_lines)
            if src_success and tgt_success:
                args.outfile.write("%s\t%s\t%s\n" %
                                   (src_url, src_crawl, json.dumps(src_loc)))
                args.outfile.write("%s\t%s\t%s\n" %
                                   (tgt_url, tgt_crawl, json.dumps(tgt_loc)))

    sys.stderr.write("Done: ")
    report_error(tgt_url, tgt_crawl, total_errors, total_lines)

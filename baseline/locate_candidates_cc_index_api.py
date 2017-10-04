#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import json
import tldextract
import re
import requests
import urllib

COMMONCRAWL_S3_URL = "https://commoncrawl.s3.amazonaws.com"
COMMONCRAWL_INDEX_URL = "http://index.commoncrawl.org"

INVALID_URL = "123"
INVALID_CRAWL = "abc"

def make_full_filename(filepath):
    return '/'.join([COMMONCRAWL_S3_URL, filepath])

def make_query_url(crawl, url):
    params = {
        "base_url": COMMONCRAWL_INDEX_URL,
        "crawl_id": crawl.replace('_', '-'),
        "url": urllib.quote(url, safe='')      # Percent encode URL.
    }

    query = "{base_url}/CC-MAIN-{crawl_id}-index?url={url}&output=json&limit=1"
    return query.format(**params)

def get_location(session, url, crawl):
    """ Returns success and location """
    query_url = make_query_url(crawl, url)
    try:
        r = session.get(query_url)
        result = r.json()
    except:
        return False, None

    try:
        data = {
            "filename": make_full_filename(result["filename"]),
            "length": result["length"],
            "mime": result["mime"],
            "offset": result["offset"]
        }
    except KeyError:
        return False, None

    return True, data


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
    parser.add_argument('-kv', help='input is a .kv.gz file',
                        default=False, action="store_true")
    args = parser.parse_args(sys.argv[1:])

    total_lines, total_errors = 0, 0
    with requests.Session() as session:
        for line in args.candidates:
            total_lines += 1
            line = line.decode("utf-8")
            if args.kv:
                # Lines have the format:
                # {domain} {url} {crawl}\t{language_data}
                url_data, _ = line.strip().split('\t')
                _, src_url, src_crawl = url_data.strip().split()
                tgt_success = False
            else:
                # Lines have the format:
                # {stripped_url} {src_url} {src_crawl} {tgt_url} {tgt_crawl}
                _, src_url, src_crawl, tgt_url, tgt_crawl = line.strip().split()

            src_success, src_loc = get_location(session, src_url, src_crawl)
            if not src_success:
                total_errors += 1
                report_error(src_url, src_crawl, total_errors, total_lines)

            if not args.kv:
                tgt_success, tgt_loc = get_location(session, tgt_url, tgt_crawl)
                if not tgt_success:
                    total_errors += 1
                    report_error(tgt_url, tgt_crawl, total_errors, total_lines)

            if src_success and tgt_success:
                args.outfile.write("%s\t%s\t%s\n" %
                                   (src_url, src_crawl, json.dumps(src_loc)))
                args.outfile.write("%s\t%s\t%s\n" %
                                   (tgt_url, tgt_crawl, json.dumps(tgt_loc)))
            elif args.kv and src_success:
                args.outfile.write("%s\t%s\t%s\n" %
                                   (src_url, src_crawl, json.dumps(src_loc)))

    sys.stderr.write("Done: ")
    report_error(tgt_url, tgt_crawl, total_errors, total_lines)

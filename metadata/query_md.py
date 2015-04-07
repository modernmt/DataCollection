#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import json
import urlparse
import tldextract
from collections import defaultdict


def get_tld(uri):
    netloc = urlparse.urlparse(uri).netloc
    tld = tldextract.extract(netloc).domain.encode('idna')
    return tld

if __name__ == "__main__":
    errors = 0
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('db', help='leveldb root directory')
    parser.add_argument('--url', help='url to search for',
                        default='')
    parser.add_argument('crawl', help='crawl id, e.g. 2013_11')
    args = parser.parse_args(sys.argv[1:])

    import leveldb
    db = leveldb.LevelDB(args.db)

    query_tld = get_tld(args.url)
    uri2crawl = defaultdict(list)
    crawl2uri = defaultdict(set)
    for key, value in db.RangeIter("%s " % query_tld):
        tld, uri, crawl = key.split(" ", 2)
        if query_tld != tld:
            break
        data = json.loads(value)
        uri2crawl[uri].append((crawl, data))
        crawl2uri[crawl].append(uri)

    sys.stderr.write("found %d unique URLs in %d crawls\n" % (len(uri2crawl),
                                                              len(crawl2uri)))
    for crawl in crawl2uri:
        sys.stderr.write("%s\t%d\n" % (crawl, len(crawl2uri[crawl])))

    for uri in uri2crawl:
        sys.stdout.write("%s\n" %uri)

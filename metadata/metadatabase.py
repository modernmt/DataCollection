#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import json


def make_full_path(crawl, folder, filename):
    return "https://aws-publicdatasets.s3.amazonaws.com/" +\
           "common-crawl/crawl-data/" + \
           "CC-MAIN-%s" % crawl.replace("_", "-") +\
           "/segments/%d" % (int(folder)) +\
           "/warc/%s" % filename.replace("warc.wat.gz", "warc.gz")

if __name__ == "__main__":
    errors = 0
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--db', help='leveldb root directory')
    parser.add_argument('--prefix', help='prefix for filename',
                        default='')
    parser.add_argument('crawl', help='crawl id, e.g. 2013_11')
    parser.add_argument('folder', help='subfolder, e.g. 1368696381249')
    args = parser.parse_args(sys.argv[1:])

    db = None
    if args.db:
        import leveldb
        db = leveldb.LevelDB(args.db)

    for line in sys.stdin:
        tld, data = line.split(" ", 1)
        data = json.loads(data)
        tld = tld.decode("utf-8").encode("idna")

        key, valuedict = None, None
        try:
            container_data = data["container"]
            offset = container_data["Offset"]
            length = container_data["Gzip-Metadata"]["Deflate-Length"]
            filename = args.prefix + container_data["Filename"]
            filename = make_full_path(args.crawl, args.folder, filename)
            uri = data["uri"]

            key = " ".join((tld, uri, args.crawl))
            valuedict = {"filename": filename, "offset:": offset,
                         "length": length}
        except KeyError:
            errors += 1

        if db is not None:
            db.Put("0 %s" % key, json.dumps(valuedict))
        else:
            sys.stdout.write("%s\t%s\n" % (key, json.dumps(valuedict)))

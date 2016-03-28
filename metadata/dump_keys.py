#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import rocksdb

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('db',
                        help='path to rocksdb')
    parser.add_argument(
        '-outfile', help='output file', type=argparse.FileType('w'),
        default=sys.stdout)
    args = parser.parse_args()

    opts = rocksdb.Options()
    opts.create_if_missing = False
    opts.max_open_files = 100
    opts.num_levels = 6
    db = rocksdb.DB(args.db, opts, read_only=True)
    it = db.iterkeys()
    it.seek_to_first()
    for key in it:
        tld, url, crawl = key.split(" ", 2)
        args.outfile.write(url + "\n")

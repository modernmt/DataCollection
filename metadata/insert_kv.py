#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import leveldb

if __name__ == "__main__":
    errors = 0
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('db', help='leveldb root directory')
    args = parser.parse_args(sys.argv[1:])

    db = leveldb.LevelDB(args.db)

    for line in sys.stdin:
        k, v = line.rstrip().split("\t", 1)
        db.Put(k, v)

    sys.stderr.write("%s" % db.GetStats())

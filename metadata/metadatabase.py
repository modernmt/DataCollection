#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import json
import tldextract
from urlparse import urlparse
import re


def make_full_path(crawl, folder, filename):
    return "https://aws-publicdatasets.s3.amazonaws.com/" +\
           "common-crawl/crawl-data/" + \
           "CC-MAIN-%s" % crawl.replace("_", "-") +\
           "/segments/%d" % (int(folder)) +\
           "/warc/%s" % filename.replace("warc.wat.gz", "warc.gz")


def get_tld(uri):
    netloc = uri.split('//',1)[1].split('/',1)[0].split(':',1)[0].split('@')[-1]
    # netloc = urlparse(uri)
    tld = tldextract.extract(netloc)
    return tld


def process_json(line, args):
    tld, data = line.split(" ", 1)
    data = json.loads(data)
    tld = tld.decode("utf-8").encode("idna")

    key, valuedict = None, None
    container_data = data["container"]
    offset = container_data["Offset"]
    length = container_data["Gzip-Metadata"]["Deflate-Length"]
    filename = args.prefix + container_data["Filename"]
    filename = make_full_path(args.crawl, args.folder, filename)
    uri = data["uri"]

    key = " ".join((tld, uri, args.crawl))
    valuedict = {"filename": filename, "offset:": offset,
                 "length": length}
    return key, valuedict


def process_cdx(line, args):
    if not line.strip():
        return None, None
    loc, timestamp, data = line.split(' ', 2)
    data = json.loads(data)
    uri = data["url"]
    tld = get_tld(uri).domain

    tld = tld.encode('idna')
    # uri = uri.encode('utf-8')

    # crawl from path, e.g. common-crawl/crawl-data/CC-MAIN-2015-14/
    crawl = data["filename"].split("/")[2][-7:].replace("-", "_")
    key = u" ".join((tld, uri, crawl)).encode("utf-8")

    filename = "https://aws-publicdatasets.s3.amazonaws.com/%s" % data[
        "filename"]
    mime_type = data.get("mime", "UNKNOWN")
    offset = data["offset"]
    length = data["length"]
    valuedict = {"filename": filename, "offset:": offset,
                 "length": length, "mime": mime_type.encode('utf-8')}
    return key, valuedict


def read_cdx(args):
    for line in sys.stdin:
        try:
            if line.count('}') == 1:
                yield process_cdx(line, args)
            else:  # sometimes several entries are on a single line
                for entry in re.findall(r"\S+\s\S+\s\{[^}]+\"\}", line):
                    yield process_cdx(entry, args)
        except ValueError:
            sys.stderr.write("Malformed line: %s\n" % line)
            raise


def read_json(args):
    for line in sys.stdin:
        try:
            yield process_json(line, args)
        except KeyError:
            pass

if __name__ == "__main__":
    errors = 0
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--db', help='leveldb root directory')
    parser.add_argument('--cdx', action='store_true',
                        help='input data is in CDX format')
    parser.add_argument('--batchsize', help='size of levelDB write batches',
                        default=100000, type=int)
    parser.add_argument('--prefix', help='prefix for filename',
                        default='')
    parser.add_argument('crawl', help='crawl id, e.g. 2013_11')
    parser.add_argument('folder', help='subfolder, e.g. 1368696381249')
    args = parser.parse_args(sys.argv[1:])

    db = None
    if args.db:
        import leveldb
        db = leveldb.LevelDB(args.db)

        batch_size = 0
        batch = leveldb.WriteBatch()

    count = 0
    kv_generator = read_cdx(args) if args.cdx else read_json(args)


    for key, valuedict in kv_generator:
        if key is None or valuedict is None:
            continue
        count += 1
        if db is not None:
            if args.batchsize > 1:
                if batch_size >= args.batchsize:
                    db.Write(batch)
                    sys.stderr.write('.')
                    batch = leveldb.WriteBatch()
                    batch_size = 0
                else:
                    batch.Put("%s" % key, json.dumps(valuedict))
                    batch_size += 1
            else:  # no batch writes
                if count % 10000 == 0:
                    sys.stderr.write('>')
                db.Put("%s" % key, json.dumps(valuedict))
        else:
            # if count % 10000 == 0:
            #     sys.stderr.write(':')
            sys.stdout.write("%s\t%s\n" %
                             (key, json.dumps(valuedict)))

    if db is not None and batch_size > 0:
        db.Write(batch, sync=True)

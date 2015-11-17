#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import json
import tldextract
from urlparse import urlparse
import re

magic_number = "df6fa1abb58549287111ba8d776733e9"


def make_full_path(crawl, folder, filename):
    return "https://aws-publicdatasets.s3.amazonaws.com/" +\
           "common-crawl/crawl-data/" + \
           "CC-MAIN-%s" % crawl.replace("_", "-") +\
           "/segments/%s" % folder +\
           "/warc/%s" % filename.replace("warc.wat.gz", "warc.gz")


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


def process_json(line, args):
    tld, data = line.split(" ", 1)
    data = json.loads(data)

    uri = data["uri"]
    key = make_key(uri, args.crawl)

    container_data = data["container"]
    offset = container_data["Offset"]
    length = container_data["Gzip-Metadata"]["Deflate-Length"]
    filename = args.prefix + container_data["Filename"]
    filename = make_full_path(args.crawl, args.folder, filename)
    mime_type = data.get("type", "UNKNOWN")
    valuedict = {"filename": filename, "offset": offset,
                 "length": length, "mime": mime_type.encode('utf-8')}
    return key, valuedict


def process_old_json(line, uri, args):
    try:
        data = json.loads(line)
    except ValueError:
        return None, None
    key = make_key(uri, args.crawl)

    if data.get("http_result", None) != 200:
        return None, None
    archive_info = data.get('archiveInfo', None)
    if not archive_info:
        return None, None
    offset = archive_info['arcFileOffset']
    length = archive_info['compressedSize']

    filename = "https://" + \
        "aws-publicdatasets.s3.amazonaws.com/" + \
        "common-crawl/parse-output/segment/" + \
        "%s" % archive_info['arcSourceSegmentId'] + \
        "/%s_%s.arc.gz" % (archive_info['arcFileDate'],
                           archive_info['arcFileParition'])

    mime_type = data.get('mime_type', '')
    if mime_type.split('/')[0] != 'text':
        # sys.stderr.write("skipping: %s %s\n" % (uri.encode('utf-8'),
        #                                         mime_type.encode('utf-8')))
        return None, None

    valuedict = {"filename": filename, "offset": offset,
                 "length": length, "mime": mime_type.encode('utf-8')}
    return key, valuedict


def make_key(url, crawl):
    tld = get_tld(url)
    if tld:
        try:
            tld = tld.domain.encode('idna')
        except UnicodeError:
            tld = '__UNKNOWN__'
    else:
        tld = '__UNKNOWN__'
    # uri = uri.encode('utf-8')
    key = u" ".join((tld, url, crawl)).encode("utf-8")
    return key


def process_cdx(line, args):
    if not line.strip():
        return None, None
    loc, timestamp, data = line.split(' ', 2)
    data = json.loads(data)
    uri = data["url"]
    # crawl from path, e.g. common-crawl/crawl-data/CC-MAIN-2015-14/
    crawl = data["filename"].split("/")[2][-7:].replace("-", "_")
    key = make_key(uri, crawl)

    filename = "https://aws-publicdatasets.s3.amazonaws.com/%s" % data[
        "filename"]
    mime_type = data.get("mime", "UNKNOWN")
    offset = data["offset"]
    length = data["length"]
    valuedict = {"filename": filename, "offset": offset,
                 "length": length, "mime": mime_type.encode('utf-8')}
    return key, valuedict


def read_cdx(args):
    for line in sys.stdin:
#        yield process_cdx(line, args)
#        continue
        try:
            if line.count('}') == 1:
                yield process_cdx(line, args)
            else:  # sometimes several entries are on a single line
                for entry in re.findall(r"\S+\s\S+\s\{[^}]+\"\}", line):
                    yield process_cdx(entry, args)
        except ValueError:
            sys.stderr.write("Malformed line: %s\n" % line)
            continue
        except Exception as e:
            sys.stderr.write("Error %s while processing: %s\n" % (e, line))
            import traceback
            sys.stderr.write(traceback.format_exc())
            sys.exit()
            continue

def read_json(args):
    for line in sys.stdin:
        try:
            yield process_json(line, args)
        except KeyError:
            pass


def read_old_json(args):
    url = None
    for line in sys.stdin:
        if line.startswith(magic_number):
            url = line.decode("utf-8").split()[1].strip()
        else:
            k, v = process_old_json(line, url, args)
            if k is not None:
                yield k, v


if __name__ == "__main__":
    errors = 0
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('--db', help='leveldb root directory')
    parser.add_argument('--cdx', action='store_true',
                        help='input data is in CDX format')
    parser.add_argument('--old', action='store_true',
                        help='old json format of 2012 crawl')
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
    if args.old:
        kv_generator = read_old_json(args)

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

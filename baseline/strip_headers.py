#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import chardet

magic_numer = "df6fa1abb58549287111ba8d776733e9"

helptext = """ Remove warc and http headers from CC downloads """
current_encoding = "utf-8"


def process_buffer(buf, fout):
    if not buf:
        return
    header = buf[0]
    skip = 0
    empty_lines = 0
    while empty_lines < 2:
        skip += 1
        if not buf[skip].strip():
            empty_lines += 1

    html = "".join(buf[skip + 1:])

    global current_encoding
    try:
        html = html.decode(current_encoding)
    except:
        try:
            encoding = chardet.detect(html)
            html = html.decode(encoding["encoding"])
            current_encoding = encoding["encoding"]
        except:
            sys.stderr.write("error decoding %s\n" % header.split()[-1])
            return

    fout.write(header)
    fout.write(html.encode("utf-8"))
    fout.write("\n")


def read_file(fin, fout):
    buf = []
    for line in fin:
        if line.startswith(magic_numer):
            process_buffer(buf, fout)
            buf = [line]
            continue
        buf.append(line)
    process_buffer(buf, fout)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=helptext)
    parser.add_argument('infile', type=argparse.FileType('r'),
                        help='source corpus', default=sys.stdin)
    parser.add_argument('outfile', type=argparse.FileType('w'),
                        help='output file', default=sys.stdout)
    args = parser.parse_args(sys.argv[1:])

    read_file(args.infile, args.outfile)

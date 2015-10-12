#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import argparse

magic_number = 'df6fa1abb58549287111ba8d776733e9'

parser = argparse.ArgumentParser()
parser.add_argument('-lang', help='language code')
args = parser.parse_args()

buf = []
keep = False
for line in sys.stdin:
    if line.startswith(magic_number):
        if buf:
            assert keep is True
            sys.stdout.write("".join(buf))

        keep = False
        buf = []

        if "language:%s" % args.lang in line.strip().split():
            keep = True

    if keep:
        buf.append(line)

if buf:
    assert keep is True
    sys.stdout.write("".join(buf))

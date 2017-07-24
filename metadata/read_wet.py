#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Reads downloaded website from tar file and writes lett format to be
processed by bitextor pipeline
"""

import sys
import chardet
from chardet.universaldetector import UniversalDetector


def guess_encoding_incremental(data):
    sys.stderr.write("running incremental chardet\n")
    detector = UniversalDetector()
    for line in data.split("\n"):
        detector.feed(line)
        if detector.done:
            break
    detector.close()
    encoding = detector.result
    return encoding["encoding"]


def guess_encoding(data):
    sys.stderr.write("running full chardet\n")
    encoding = chardet.detect(data)
    return encoding["encoding"]


def convert_to_utf8(data, force_chardet=False):
    encoding = "utf-8"
    try:
        if force_chardet:
            raise
        data = data.decode(encoding)
    except:
        encoding = guess_encoding_incremental(data)
        try:
            data = data.decode(encoding)
        except:
            encoding = guess_encoding(data)
            try:
                data = data.decode(encoding)
            except:
                sys.stderr.write("Fallback: ignoring errors.\n")
                return data.decode("utf-8", errors='ignore')
    # sys.stderr.write("Detected encoding: %s\n"
    #                  % encoding)
    return data

magic_number = "df6fa1abb58549287111ba8d776733e9"


def process_buffer(uri, buf):
    sys.stdout.write("%s uri:%s\n" % (magic_number, uri))
    buf = "".join(buf)
    buf = convert_to_utf8(buf)
    sys.stdout.write(buf.encode("utf-8"))

in_header, in_content = False, False
uri, buf = None, []

skip = True

for line in sys.stdin:
    assert not (in_header and in_content)
    assert not (in_header and buf)
    assert not (in_content and not uri)

    if line.startswith("WARC-Type: conversion"):
        in_header = True
        in_content = False
        uri, buf = None, []
        continue

    if in_header:
        if line.startswith("WARC-Target-URI:"):
            uri = line.split(" ", 1)
            if len(uri) > 1:
                uri = uri[1].strip()
        if not line.strip():
            in_content = True
            in_header = False
        continue

    if in_content:
        if not line.strip():
            if uri:
              process_buffer(uri, buf)
            uri, buf = None, []
            in_content = False
        else:
            buf.append(line)

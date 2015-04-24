#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import json
import tldextract
from urlparse import urlparse


valid_paths = ["A", "IMG"]


def valid_link(link):
    if "path" not in link:
        return False
    if not link["path"].split("@", 1)[0] in valid_paths:
        return False
    return True

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-nolinks', action='store_true',
                        help='skip link extraction')
    args = parser.parse_args(sys.argv[1:])

    for line in sys.stdin:
        if not line.startswith("{"):
            continue
        try:
            d = json.loads(line)
        except ValueError:
            continue

        uri, links, container, content_type = None, None, None, None
        try:
            container = d["Container"]
            content_type = d["Envelope"]["Payload-Metadata"][
                "HTTP-Response-Metadata"]["Headers"][
                "Content-Type"]
            uri = d["Envelope"]["WARC-Header-Metadata"]["WARC-Target-URI"]
            links = d["Envelope"]["Payload-Metadata"][
                "HTTP-Response-Metadata"]["HTML-Metadata"]["Links"]
        except KeyError:
            continue

        res = {"container": container, "uri": uri, "type": content_type}
        if not args.nolinks:
            res["links"] = links
        try:
            tld = tldextract.extract(urlparse(uri).netloc)
        except UnicodeError:
            continue
        print tld.domain.encode("utf8", "ignore"), json.dumps(res)

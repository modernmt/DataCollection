#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import json
import tldextract
from urlparse import urlparse


if __name__ == "__main__":
    for line in sys.stdin:
        if not line.startswith("{"):
            continue
        try:
            d = json.loads(line)
        except ValueError:
            continue

        uri, links = None, None
        try:
            container = d["Container"]
            uri = d["Envelope"]["WARC-Header-Metadata"]["WARC-Target-URI"]
            links = d["Envelope"]["Payload-Metadata"][
                "HTTP-Response-Metadata"]["HTML-Metadata"]["Links"]
        except KeyError:
            continue

        if not links:
            continue

        res = {"uri": uri, "container": container, "links": links}
        try:
            tld = tldextract.extract(urlparse(uri).netloc)
        except UnicodeError:
            continue
        print tld.domain.encode("utf8", "ignore"), json.dumps(res)

#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import json
import tldextract
from urlparse import urlparse


valid_paths = ["A", "IMG"]

def valid_link(link):
    if not "path" in link:
        return False
    if not link["path"].split("@",1)[0] in valid_paths:
        return False
    return True

if __name__ == "__main__":
    for line in sys.stdin:
        if not line.startswith("{"):
            continue
        d = json.loads(line)

        uri, links = None, None
        try:
            uri = d["Envelope"]["WARC-Header-Metadata"]["WARC-Target-URI"]
            links = d["Envelope"]\
                     ["Payload-Metadata"]\
                     ["HTTP-Response-Metadata"]\
                     ["HTML-Metadata"]\
                     ["Links"]
            # links = [link for link in links if valid_link(link)]
        except KeyError:
            continue

        if not links:
            continue

        res = {"uri": uri, "links": links}
        tld = tldextract.extract(urlparse(uri).netloc)
        print tld.domain.encode("utf8", "ignore") , json.dumps(res)

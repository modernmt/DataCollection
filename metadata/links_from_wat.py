#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import json
import tldextract
from urlparse import urlparse, urlsplit, urlunsplit
from urlparse import urljoin
from urllib import quote, quote_plus


def is_pdf_link(link):
    if "path" not in link:
        return False
    if link["path"].split("@", 1)[0] != 'A':
        return False
    if not link["url"].lower().endswith('.pdf'):
        return False
    return True


def quote_spaces(s):
    if isinstance(s, unicode):
        s = s.encode('utf-8', 'ignore')
    scheme, netloc, path, qs, anchor = urlsplit(s)
    path = quote(path, '/%()')
    qs = quote_plus(qs, ':&=')
    return urlunsplit((scheme, netloc, path, qs, anchor))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-nolinks', action='store_true',
                        help='skip link extraction')
    parser.add_argument('-pdf', action='store_true',
                        help='extract only PDF links')
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

        if args.pdf:
            for link in links:
                if is_pdf_link(link):
                    try:
                        url = link['url']
                        # url = quote_spaces(url)
                        text = link.get('text', "")
                        text = u' '.join(text.split())
                        output = "%s\t%s\t%s\n" % (uri.encode('utf-8','ignore'),
                                                   url.encode('utf-8','ignore'),
                                                   text.encode('utf-8','ignore'))
                        sys.stdout.write(output)
                    except UnicodeDecodeError:
                        continue
                     
            continue

        res = {"container": container, "uri": uri, "type": content_type}
        if not args.nolinks:
            res["links"] = links
        try:
            tld = tldextract.extract(urlparse(uri).netloc)
        except UnicodeError:
            continue
        print tld.domain.encode("utf8", "ignore"), json.dumps(res)

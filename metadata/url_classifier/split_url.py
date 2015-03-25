#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from urlparse import urlparse, parse_qsl
import tldextract
import re

# example: df6fa1abb58549287111ba8d776733e9 uri:http://49ersnews.com/forum/index.php?showtopic=36414&st=15&p=563397&k=880ea6a14ea49e853634fbdc5015a024&settingNewSkin=18&k=880ea6a14ea49e853634fbdc5015a024&settingNewSkin=18 encoding:iso-8859-1 tld:com domain:49ersnews bytes:1180

magic_number = "df6fa1abb58549287111ba8d776733e9"

def url_components(uri):
    components = set()
    parts = urlparse(uri)

    # extract subdomain, domain, suffic from full domain
    # e.g.: tldextract.extract('radio1.bbc.co.uk')
    # gives ExtractResult(subdomain='radio1', domain='bbc', suffix='co.uk')
    domain_parts = tldextract.extract(parts.netloc)
    if domain_parts.subdomain:
        components.add("sub:%s" %domain_parts.subdomain)
    if domain_parts.domain:
        components.add("domain:%s" %domain_parts.domain)
    if domain_parts.suffix:
        components.add("tld:%s" %domain_parts.suffix)

    for dn, directory in enumerate(parts.path.split('/')):
        if directory and len(directory) < 10:
            components.add("d_%d:%s" %(dn, directory))
        n = 0
        for path_element in re.split('[^0-9A-Za-z=]+', directory):
            if path_element:
                components.add("p%d:%s" %(n, path_element))
                components.add("path:%s" %(path_element))
                n += 1

    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        if len(value) < 20:
            components.add("query:%s=%s" %(key, value))

    if '' in components:
        components.remove('')
    return components

def filter_components(components, max_length):
    return [c for c in components if len(c.split(':',1)[1]) < max_length]

def get_languages(buffer):
    return [(lang, int(percentage), int(num_bytes)) \
            for lang, percentage, num_bytes in \
               [line.split() for line in buffer]]

def process_buffer(buffer, max_length, max_english):
    if not buffer or len(buffer) < 2:
        return
    assert buffer[0].startswith(magic_number)

    languages = get_languages(buffer[1:])
    percent_english = 0
    for lang, percent, num_bytes in languages:
        if lang == "ENGLISH":
            percent_english = percent
            break
    if percent_english > max_english:
        return

    uri = buffer[0].split(' ', 2)[1].split(':', 1)[1]
    # print "uri:", uri
    components = url_components(uri)
    components = filter_components(components, max_length)
    print u"\n".join(components).encode("utf-8")



if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--max_english', default=100, type=int, 
        help='ignore pages with higher percentage of ENLGISH text')
    parser.add_argument('--max_length', default=20, type=int, 
        help='ignore components longer than this')
    args = parser.parse_args(sys.argv[1:])

    buffer = []
    for line in sys.stdin:
        line = line.decode("utf-8", "ignore")
        if line.startswith(magic_number):
            process_buffer(buffer, args.max_length, args.max_english)
            buffer = [line]
        elif buffer:
            buffer.append(line)
    process_buffer(buffer, args.max_length, args.max_english)


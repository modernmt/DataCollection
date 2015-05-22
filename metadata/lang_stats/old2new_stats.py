#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import tldextract

from cld2helper import read_cld2_languages


def get_domain(netloc):
    extract = tldextract.extract(netloc)
    return ".".join((extract.domain, extract.suffix)).encode('idna')


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('infile', nargs='?', type=argparse.FileType('r'))
    args = parser.parse_args()

    name2code, code2name = read_cld2_languages(args.infile)

    for line in sys.stdin:
        domain, language, num_bytes = line.split()
        assert language in code2name
        language = code2name[language]
        # domain = get_domain(domain)

        sys.stdout.write("%s %s %d\n" % (domain, language, int(num_bytes)))


# en.wikipedia.org xx-Kali 274

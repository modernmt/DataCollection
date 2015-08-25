#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from strip_language_from_uri import LanguageStripper
import urlparse

correct, wrong = [], []


def strip_uri(uri, language_stripper):
    parsed_uri = urlparse.urlparse(uri)

    matched_language = language_stripper.match(parsed_uri.path)
    if not matched_language:
        matched_language = language_stripper.match(parsed_uri.query)
        assert matched_language

    stripped_path = language_stripper.strip(parsed_uri.path)
    stripped_query = language_stripper.strip(parsed_uri.query)
    stripped_uri = urlparse.ParseResult(parsed_uri.scheme,
                                        parsed_uri.netloc,
                                        stripped_path,
                                        parsed_uri.params,
                                        stripped_query,
                                        parsed_uri.fragment).geturl()
    return matched_language, stripped_uri

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        'infile', type=argparse.FileType('r'), default=sys.stdin)
    parser.add_argument(
        '--outfile', type=argparse.FileType('w'))
    parser.add_argument('-filter', action="store_true")
    args = parser.parse_args()
    stripper = LanguageStripper()

    source_uris, target_uris = set(), set()

    for line in args.infile:
        source_uri, target_uri, source, target, score = line.split("\t")
        source_lang, stripped_source_uri = strip_uri(source_uri, stripper)
        target_lang, stripped_target_uri = strip_uri(target_uri, stripper)
        source_uris.add(source_uri)
        target_uris.add(target_uri)
        if stripped_source_uri != stripped_target_uri:
            wrong.append((stripped_source_uri, stripped_target_uri))
        else:
            if args.outfile:
                args.outfile.write(line)
            correct.append((stripped_source_uri, stripped_target_uri))

    print "found %s source and %s target uris" % (len(source_uris), len(target_uris))

    total = len(wrong) + len(correct)
    total_unique = len(set(wrong).union(set(correct)))
    if wrong:
        print "Wrong: ",  len(wrong), len(set(wrong))
    if correct:
        print "Correct", len(correct), len(set(correct))
    if total > 0:
        print "Acc1", float(len(wrong)) / total
        print "Acc2", float(len(set(wrong))) / total_unique

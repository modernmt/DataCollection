#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from difflib import get_close_matches, SequenceMatcher
from collections import defaultdict
from languagestripper import LanguageStripper
import urlparse


def read_urls(infile, source_lang='fr', target_lang='en'):
    source_urls, target_urls, other_urls = [], [], []
    for line in infile:
        line = line.strip().split('\t')
        if len(line) != 2:
            continue
        lang, url = line
        url = normalize_url(url.strip())
        if lang == source_lang:
            source_urls.append(url)
        elif lang == target_lang:
            target_urls.append(url)
        else:
            other_urls.append(url)
    return source_urls, target_urls, other_urls


def read_reference(infile):
    devset = []
    for line in infile:
        source_url, target_url = line.strip().split("\t")
        # devset.append(sorted([source_url, target_url]))
        devset.append((source_url, target_url))
    return devset


def n_longest(l, n=2, discounted=None):
    items = [[len(i), i] for i in l]

    if discounted:
        for j, i in enumerate(l):
            if i in discounted:
                items[j][0] -= 100

    items.sort(reverse=True)
    return [i for _, i in items[:n]]


def normalize_url(url):
    """ It seems some URLs have an empty query string.
    This function removes the trailing '?' """
    url = url.rstrip('?')
    if not url.startswith("http://"):
        url = ''.join(("http://", url))
    return url


def get_netloc(uri):
    parsed_uri = urlparse.urlparse(uri)
    netloc = parsed_uri.netloc
    if '@' in netloc:
        netloc = netloc.split('@')[1]
    if ':' in netloc:
        netloc = netloc.split(':')[0]
    return netloc


def strip_urls(urls, lang):
    stripped = defaultdict(set)
    language_stripper = LanguageStripper(languages=[lang])

    for url in urls:
        stripped_url, success = language_stripper.strip_uri(url)
        if success:
            stripped[stripped_url].add(url)

    return stripped


def find_matches(source_stripped, target_stripped):
    matches = {}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-sourcelang', default='fr')
    parser.add_argument('-targetlang', default='en')
    parser.add_argument('-devset',
                        help='correct pairs in dev set',
                        type=argparse.FileType('r'))
    parser.add_argument('-pairs',
                        help='write pairs to this file',
                        type=argparse.FileType('w'))
    parser.add_argument('-wins',
                        help='write correct pairs to this file',
                        type=argparse.FileType('w'))
    parser.add_argument('-fails',
                        help='write fails to this file',
                        type=argparse.FileType('w'))
    parser.add_argument('-nostrip', help='accept only exact matches',
                        action='store_true')
    parser.add_argument('-augment', help='augment matches with similar URLs',
                        action='store_true')
    args = parser.parse_args(sys.argv[1:])

    source_urls, target_urls, other_urls = read_urls(
        sys.stdin, args.sourcelang, args.targetlang)

    sys.stderr.write("Read %d/%d/%d %s/%s/other URLs from stdin\n" % (
        len(source_urls), len(target_urls), len(other_urls), args.sourcelang,
        args.targetlang))

    devset = None
    if args.devset:
        devset = read_reference(args.devset)

        sys.stderr.write("Check if all pairs in devset can be reached\n")
        unreachable = []
        for source_url, target_url in devset:
            if source_url not in source_urls:
                sys.stderr.write(
                    "Source URL %s not found in candidate URLs\n" % source_url)
                unreachable.append(source_url)
            if target_url not in target_urls:
                sys.stderr.write(
                    "Target URL %s not found in candidate URLs\n" % target_url)
                unreachable.append(target_url)

        sys.stderr.write("%d urls missing from candidates\n" %
                         (len(unreachable)))

    source_stripped = strip_urls(source_urls, args.sourcelang)
    target_stripped = strip_urls(target_urls, args.targetlang)
    sys.exit()

    unstripped_urls = set(urls.keys())

    for lang in args.languages:
        language_stripper = LanguageStripper(languages=[lang])
        # language_stripper = LanguageStripper()

        for url in unstripped_urls:

            stripped_url, success = language_stripper.strip_uri(url)
            if success:
                urls[stripped_url].add(url)

            # if stripped_url != url:
            #     stripped_urls[stripped_url] = url

    n_pairs = 0
    for key, mapped_urls in urls.iteritems():
        if len(mapped_urls) > 1:
            n_pairs += 1
    sys.stderr.write("Found %s pairs\n" % (n_pairs))

    pairs = {}
    for key, mapped_urls in urls.iteritems():
        mapped_urls = n_longest(mapped_urls, n=2, discounted=unstripped_urls)
        if len(mapped_urls) == 2:
            # print "\t".join(list(mapped_urls))
            u1, u2 = mapped_urls
            assert u1 != u2
            if u1 in pairs and pairs[u1] != u2:
                sys.stderr.write("%s -> %s in pairs: %s\n" %
                                 (u1, u2, pairs[u1]))
            # assert u1 not in pairs
            if u2 in pairs and pairs[u2] != u1:
                sys.stderr.write("%s -> %s in pairs: %s\n" %
                                 (u2, u1, pairs[u2]))
            # assert u2 not in pairs
            pairs[u1] = u2
            pairs[u2] = u1
            if args.pairs:
                # if u1 > u2:
                #     u1, u2 = u2, u1
                args.pairs.write("%s\t%s\n" % (u1, u2))
        # elif len(mapped_urls) > 2:
        # print "Found more than 2 matching urls:", "\t".join(mapped_urls)
        #     for i, u1 in enumerate(mapped_urls):
        #         for u2 in mapped_urls[i + 1:]:
        #             args.pairs.write("%s\t%s\n" % (u1, u2))

    print "Found %d pairs" % (len(pairs) / 2)
    # devset = dict(devset)

    # adding close matches for stripped urls:
    if args.augment:
        netloc2strippedurls = defaultdict(list)
        for url in stripped_urls.keys():
            netloc2strippedurls[get_netloc(url)].append(url)

        n_stripped_added = 0
        for stripped_url, url in stripped_urls.iteritems():
            if url not in pairs:
                for cand in get_close_matches(stripped_url,
                                              netloc2strippedurls[
                                                  get_netloc(url)],
                                              100, cutoff=0.9):
                    if stripped_urls[cand] in pairs:
                        continue
                    u1 = url
                    u2 = stripped_urls[cand]
                    if u1 == u2:
                        continue
                    pairs[u1] = u2
                    pairs[u2] = u1
                    distance = SequenceMatcher(None, u1, u2).ratio()
                    print "Adding %f %s <-> %s" % (distance, u1, u2)
                    n_stripped_added += 1
                    if args.pairs:
                        args.pairs.write("%s\t%s\n" % (u1, u2))
                    break
        print "Added %d pairs from similar looking stripped urls" % (
            n_stripped_added)
        print "Total %d pairs" % (len(pairs) / 2)

    correct = 0
    no_matching = []
    mismatch = []
    if devset:
        for u1, u2 in devset:
            if u1 not in pairs:
                no_matching.append(u1)
                args.fails.write("NO MATCH: %s [expected: %s]\n" % (u1, u2))
                if u2 in pairs:
                    args.fails.write(
                        "-> U2 %s found with %s [expected %s]\n" % (u2,
                                                                    pairs[u2],
                                                                    u1))
            elif pairs[u1] != u2:
                mismatch.append((u1, u2, pairs[u1]))
                if args.fails:
                    args.fails.write("MISMATCH: %s\t->\t%s\texpected: %s\n" %
                                     (u1, pairs[u1], u2))
            else:
                assert pairs[u1] == u2
                if args.wins:
                    args.wins.write("%s\t%s\n" % (u1, u2))
                correct += 1

    print "Correct: %d/%d = %f" % (correct, len(devset), float(correct) /
                                   len(devset))

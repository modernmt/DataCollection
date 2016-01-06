#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from difflib import get_close_matches, SequenceMatcher
from collections import defaultdict
from languagestripper import LanguageStripper
import urlparse


def read_urls(infile, source_lang='fr', target_lang='en', mapping=None):
    filename2url = {}
    if mapping:
        for line in mapping:
            filename, url = line.strip().split('\t')
            assert filename not in filename2url, \
                "duplicate entry: %s\n" % filename
            filename2url[filename] = url

    source_urls, target_urls, other_urls = [], [], []
    for line in infile:
        line = line.strip().split('\t')
        if len(line) != 2:
            continue
        lang, url = line
        # if filename2url[url] == "unknown_url":
        #     print "Unknown url: ", url
        if filename2url and filename2url[url] != "unknown_url":
            url = filename2url[url]
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


def strip_urls(urls, lang=None):
    stripped = defaultdict(set)
    if lang is not None:
        language_stripper = LanguageStripper(languages=[lang])
        for url in urls:
            stripped_url, success = language_stripper.strip_uri(
                url, expected_language=lang)
            if success:
                # if stripped_url in stripped:
                #     print stripped_url, url, stripped[stripped_url]
                stripped[stripped_url].add(url)

    else:
        language_stripper = LanguageStripper(strip_query_variables=True)
        for url in urls:
            stripped_url, success = language_stripper.strip_uri(
                url)
            if stripped_url != url:
                stripped[stripped_url].add(url)

            stripped_url, success = language_stripper.strip_uri(
                url, remove_index=True)
            if stripped_url != url:
                stripped[stripped_url].add(url)
    return stripped


def find_pairs(source_urls, target_urls,
               source_stripped, target_stripped,
               devset):
    pairs = []
    # stripped source url matches unstripped target url
    # e.g. mypage.net/index.html?lang=fr <-> mypage.net/index.html
    for stripped_source_url in set(
            source_stripped.iterkeys()).intersection(target_urls):
        tu = stripped_source_url
        for su in source_stripped[stripped_source_url]:
            pairs.append((su, tu))
    npairs = len(set(pairs))
    sys.stderr.write(
        "Found %d %s pairs (total: %d) covering %d pairs from devset\n"
        % (npairs, "stripped source + unmodified target",
           npairs, len(set(devset).intersection(pairs))))

    # stripped target url matches unstripped source url.
    # e.g. lesite.fr/en/bonsoir <-> lesite.fr/bonsoir
    for stripped_target_url in set(
            target_stripped.iterkeys()).intersection(source_urls):
        su = stripped_target_url
        for tu in target_stripped[stripped_target_url]:
            pairs.append((su, tu))

    oldpairs = npairs
    npairs = len(set(pairs))
    sys.stderr.write(
        "Found %d %s pairs (total: %d) covering %d pairs from devset\n"
        % (npairs - oldpairs, "stripped target + unmodified source",
           npairs, len(set(devset).intersection(pairs))))

    # stripped source url matches stripped target url
    # e.g. page.net/fr <-> page.net/en
    oldpairs = len(pairs)
    for stripped_source_url, source_url in source_stripped.iteritems():
        if stripped_source_url in target_stripped:
            for su in source_url:
                for tu in target_stripped[stripped_source_url]:
                    pairs.append((su, tu))

    oldpairs = npairs
    npairs = len(set(pairs))
    sys.stderr.write(
        "Found %d %s pairs (total: %d) covering %d pairs from devset\n"
        % (npairs - oldpairs, "stripped source + stripped target",
           npairs, len(set(devset).intersection(pairs))))

    return pairs

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
    parser.add_argument('-mapping', type=argparse.FileType('r'),
                        help='mapping of filename to actual URLs')
    args = parser.parse_args(sys.argv[1:])

    source_urls, target_urls, other_urls = read_urls(
        sys.stdin, args.sourcelang, args.targetlang, mapping=args.mapping)

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
    print "%d/%d stripped source/target urls" % (len(source_stripped),
                                                 len(target_stripped))

    pairs = find_pairs(source_urls, target_urls,
                       source_stripped, target_stripped,
                       devset)
    sys.stderr.write("Total: %d candidate pairs\n" % (len(set(pairs))))

    oldpairs = len(set(pairs))
    sys.stderr.write("Running agressive stripping for higher recall\n")
    source_stripped = strip_urls(source_urls)
    target_stripped = strip_urls(target_urls)
    print "%d/%d stripped source/target urls" % (len(source_stripped),
                                                 len(target_stripped))

    pairs.extend(find_pairs(source_urls, target_urls,
                            source_stripped, target_stripped,
                            devset))
    sys.stderr.write("Added %d pairs (total: %d)\n"
                     % (len(set(pairs)) - oldpairs, len(set(pairs))))

    # Filter pairs so that every url only occurs once
    pairs_s2t, pairs_t2s = {}, {}
    for su, tu in pairs:
        if su not in pairs_s2t and tu not in pairs_t2s:
            pairs_s2t[su] = tu
            pairs_t2s[tu] = su

            if args.pairs:
                args.pairs.write("%s\t%s\n" % (su, tu))

    sys.stderr.write("Keeping %d pairs\n" % (len(pairs_s2t)))
    sys.stderr.write("%d pairs from devset\n" %
                     (len(set(devset).intersection(pairs_s2t.items()))))

    # write wins and fails
    if args.fails:
        for su, tu in set(devset).difference(pairs_s2t.items()):
            if su in pairs_s2t:
                args.fails.write("S2T MISMATCH: %s\t->\t%s\texpected: %s\n" %
                                 (su, pairs_s2t[su], tu))
            if tu in pairs_t2s:
                args.fails.write("T2S MISMATCH: %s\t->\t%s\texpected: %s\n" %
                                 (tu, pairs_t2s[tu], tu))
            if su not in pairs_s2t and tu not in pairs_t2s:
                args.fails.write("Missing: %s\t->\t%s\n" %
                                 (su, tu))

            if (su, tu) in pairs:
                args.fails.write("Was in pairs\n")

    if args.wins:
        for su, tu in set(devset).intersection(pairs_s2t.items()):
            args.wins.write("%s\t%s\n" % (su, tu))

    sys.exit()

    # unstripped_urls = set(urls.keys())

    # for lang in args.languages:
    #     language_stripper = LanguageStripper(languages=[lang])
    # language_stripper = LanguageStripper()

    #     for url in unstripped_urls:

    #         stripped_url, success = language_stripper.strip_uri(url)
    #         if success:
    #             urls[stripped_url].add(url)

    # if stripped_url != url:
    # stripped_urls[stripped_url] = url

    # n_pairs = 0
    # for key, mapped_urls in urls.iteritems():
    #     if len(mapped_urls) > 1:
    #         n_pairs += 1

    # pairs = {}
    # for key, mapped_urls in urls.iteritems():
    #     mapped_urls = n_longest(mapped_urls, n=2, discounted=unstripped_urls)
    #     if len(mapped_urls) == 2:
    # print "\t".join(list(mapped_urls))
    #         u1, u2 = mapped_urls
    #         assert u1 != u2
    #         if u1 in pairs and pairs[u1] != u2:
    #             sys.stderr.write("%s -> %s in pairs: %s\n" %
    #                              (u1, u2, pairs[u1]))
    # assert u1 not in pairs
    #         if u2 in pairs and pairs[u2] != u1:
    #             sys.stderr.write("%s -> %s in pairs: %s\n" %
    #                              (u2, u1, pairs[u2]))
    # assert u2 not in pairs
    #         pairs[u1] = u2
    #         pairs[u2] = u1
    #         if args.pairs:
    # if u1 > u2:
    # u1, u2 = u2, u1
    #             args.pairs.write("%s\t%s\n" % (u1, u2))
    # elif len(mapped_urls) > 2:
    # print "Found more than 2 matching urls:", "\t".join(mapped_urls)
    # for i, u1 in enumerate(mapped_urls):
    # for u2 in mapped_urls[i + 1:]:
    # args.pairs.write("%s\t%s\n" % (u1, u2))

    # print "Found %d pairs" % (len(pairs) / 2)
    # devset = dict(devset)

    # adding close matches for stripped urls:
    # if args.augment:
    #     netloc2strippedurls = defaultdict(list)
    #     for url in stripped_urls.keys():
    #         netloc2strippedurls[get_netloc(url)].append(url)

    #     n_stripped_added = 0
    #     for stripped_url, url in stripped_urls.iteritems():
    #         if url not in pairs:
    #             for cand in get_close_matches(stripped_url,
    #                                           netloc2strippedurls[
    #                                               get_netloc(url)],
    #                                           100, cutoff=0.9):
    #                 if stripped_urls[cand] in pairs:
    #                     continue
    #                 u1 = url
    #                 u2 = stripped_urls[cand]
    #                 if u1 == u2:
    #                     continue
    #                 pairs[u1] = u2
    #                 pairs[u2] = u1
    #                 distance = SequenceMatcher(None, u1, u2).ratio()
    #                 print "Adding %f %s <-> %s" % (distance, u1, u2)
    #                 n_stripped_added += 1
    #                 if args.pairs:
    #                     args.pairs.write("%s\t%s\n" % (u1, u2))
    #                 break
    #     print "Added %d pairs from similar looking stripped urls" % (
    #         n_stripped_added)
    #     print "Total %d pairs" % (len(pairs) / 2)

    # correct = 0
    # no_matching = []
    # mismatch = []
    # if devset:
    #     for u1, u2 in devset:
    #         if u1 not in pairs:
    #             no_matching.append(u1)
    #             args.fails.write("NO MATCH: %s [expected: %s]\n" % (u1, u2))
    #             if u2 in pairs:
    #                 args.fails.write(
    #                     "-> U2 %s found with %s [expected %s]\n" % (u2,
    #                                                                 pairs[u2],
    #                                                                 u1))
    #         elif pairs[u1] != u2:
    #             mismatch.append((u1, u2, pairs[u1]))
    #             if args.fails:
    #                 args.fails.write("MISMATCH: %s\t->\t%s\texpected: %s\n" %
    #                                  (u1, pairs[u1], u2))
    #         else:
    #             assert pairs[u1] == u2
    #             if args.wins:
    #                 args.wins.write("%s\t%s\n" % (u1, u2))
    #             correct += 1

    # print "Correct: %d/%d = %f" % (correct, len(devset), float(correct) /
    #                                len(devset))

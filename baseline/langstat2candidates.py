#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import re
import urlparse
import json

from languagestripper import LanguageStripper

helptext = """
Take language statistics from stdin and write candidates,
i.e. url with some language identifier removed to stdout.

If a list of pre-generated candidates is given, only those
stripped urls that also occur in the list of candidates will
be written.

Input format:
tld url crawl<TAB>json_data

Example:
ex http://www.ex.com/id.html 2014_42  {"languages": [["en", 1000]]}

"""


def stoi(s):
    """ works like int(s) but also accepts floats and scientific notation """
    try:
        return int(s)
    except ValueError:
        return int(float(s))


def print_match(matching_uri, orig_uri, crawl, candidates):
    """ machting_uri is the one found in candidates, possibly
        after chopping off bits.
        orig_uri is the unmodified source uri
        crawl is the crawl what contains orig_uri
        candidates are target candidates
    """
    assert matching_uri in candidates
    line = candidates[matching_uri]
    stripped, lang, tld_and_orig_crawl, langdist = line.split('\t', 3)
    tld, candidate_orig, candidate_crawl = tld_and_orig_crawl.split(' ')
    if candidate_orig == orig_uri:
        return
    else:
        print matching_uri, orig_uri, crawl, candidate_orig, candidate_crawl


def read_candidates(infile, valid_hosts=None):
    """ Read candidate urls from previous runs of this script """
    candidates = {}
    for line in infile:
        # working around an old preprocessing error
        if line.startswith('http://://'):
            line = line.replace('http://://', 'http://')

        try:
            stripped, lang, tld_and_orig_crawl, langdist = line.split('\t', 3)
            tld, candidate_orig, candidate_crawl = tld_and_orig_crawl.split(
                ' ')
        except:
            sys.stderr.write("Malformed input: '%s'" % line)
            continue

        if valid_hosts and not netloc(candidate_orig) in valid_hosts:
            continue

        # The same uri can appear in different crawls.
        # Can also appear multiple time in the same crawl, ignore this
        # candidates["%s\t%s" % (crawl, stripped)] = line
        candidates[stripped] = line
    return candidates


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-lang', help='language codes')
    parser.add_argument('-candidates',
                        help='candidates from url strippper',
                        type=argparse.FileType('r'))
    parser.add_argument('-nostrip', help='accept only exact matches',
                        action='store_true')
    args = parser.parse_args(sys.argv[1:])

    candidates = {}
    if args.candidates:
        candidates = read_candidates(args.candidates)

    language_stripper = LanguageStripper(languages=[args.lang])

    for line in sys.stdin:
        split_line = line.split('\t')
        k, v = split_line[-2:]
        tld, uri, crawl = k.split(' ')

        if len(split_line) == 2 and args.nostrip \
                and candidates and uri not in candidates:
            # We're matching candidates agains a KV list without stripping,
            # i.e. target candidate is stripped and source candidate isn't
            # This allows for a cheap reject.
            continue

        languages = json.loads(v)['languages']

        if args.lang not in [l for l, b in languages]:
            # this page does not have text in the language
            # we're looking for
            continue

        if len(split_line) == 4:  # Input is output of previous run
            stripped_uri, _lang = line[:2]
            assert candidates, 'need to supply candidates\n'
            assert args.nostrip, 'no need to strip again\n'
            if stripped_uri in candidates:
                print_match(stripped_uri, uri, crawl, candidates)
                continue

        if candidates and uri in candidates:
            print_match(uri, uri, crawl, candidates)
            continue

        parsed_uri = urlparse.urlparse(uri)

        matched_languages = [language_stripper.match(parsed_uri.path),
                             language_stripper.match(parsed_uri.query)]

        if args.lang not in matched_languages:
            # we removed a bit of the URL but is does not support our
            # hope to find args.lang, e.g. removed /fr/ when we were looking
            # for Italian pages.
            continue

        stripped_path = language_stripper.strip_path(parsed_uri.path)
        stripped_path = re.sub(r'//+', '/', stripped_path)
        stripped_path = re.sub(r'__+', '_', stripped_path)
        stripped_path = re.sub(r'/_+', '/', stripped_path)
        stripped_path = re.sub(r'_/', '/', stripped_path)
        stripped_path = re.sub(r'--+', '-', stripped_path)

        # remove new trailing /
        if stripped_path and stripped_path[-1] == '/' \
                and parsed_uri.path and parsed_uri.path[-1] != '/':
            stripped_path = stripped_path[:-1]

        # add removed trailing /
        if not stripped_path.endswith('/') and parsed_uri.path.endswith('/'):
            stripped_path += '/'

        stripped_query = language_stripper.strip_query(parsed_uri.query)

        netloc = parsed_uri.netloc
        if '@' in netloc:
            netloc = netloc.split('@')[1]
        if ':' in netloc:
            netloc = netloc.split(':')[0]
        if not netloc:
            continue

        stripped_uri = urlparse.ParseResult(scheme="http",
                                            netloc=parsed_uri.netloc,
                                            path=stripped_path,
                                            params='',
                                            query=stripped_query,
                                            fragment='').geturl()

        if candidates:
            if stripped_uri in candidates:
                print_match(stripped_uri, uri, crawl, candidates)
                continue
        else:
            try:
                sys.stdout.write("\t".join([stripped_uri, args.lang, line]))
                # line still has the newline
            except UnicodeEncodeError:
                pass

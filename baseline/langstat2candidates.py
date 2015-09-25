#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import re
import urlparse
import urllib
import json

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


class LanguageStripper(object):

    def __init__(self, languages=None):
        self.code_to_language = {}
        for code in ["arabic", "ara", "ar"]:
            self.code_to_language[code] = "ar"
        for code in ["bulgarian", "bul", "bg"]:
            self.code_to_language[code] = "bg"
        for code in ["czech", "cze", "cz", "cs"]:
            self.code_to_language[code] = "cs"
        for code in ["deutsch", "german", "ger", "deu", "de"]:
            self.code_to_language[code] = "de"
        for code in ["english", "eng", "en"]:
            self.code_to_language[code] = "en"
        for code in ["espanol", "spanish", "spa", "esp", "es"]:
            self.code_to_language[code] = "es"
        for code in ["french", "francais", "fran", "fra", "fre", "fr"]:
            self.code_to_language[code] = "fr"
        for code in ["chinese", "chi", "zh"]:
            self.code_to_language[code] = "zh"
        # new, not in "Dirt-Cheap"-paper
        for code in ["tedesco", "de-de", "de-ch", "de-at", "de-li", 'de-lu',
                     'allemand']:
            self.code_to_language[code] = "de"
        for code in ["fr-be", "fr-ca", "fr-fr", "fr-lu", "fr-ch"]:
            self.code_to_language[code] = "fr"
        for code in ["italian", "italiano", "ital", 'ita', 'it-it', 'it-ch',
                     'it']:
            self.code_to_language[code] = "it"
        for code in ["en-en", "en-us", "en-uk", 'en-ca', 'en-bz', 'en-ab',
                     'en-in', 'en-ie', 'en-jm', 'en-nz', 'en-ph', 'en-za',
                     'en-tt', 'inglese']:
            self.code_to_language[code] = "en"

        if languages is not None:
            kv_pairs = [(k, v) for k, v in self.code_to_language.items()
                        if v in languages]
            self.code_to_language = dict(kv_pairs)

        for code, lang in self.code_to_language.items():
            # add de_de from de-de
            self.code_to_language[code.replace('-', '_')] = lang

        keys = self.code_to_language.keys()
        keys.sort(key=len, reverse=True)
        regexp_string = "(?<![a-zA-Z0-9])(?:%s)(?![a-zA-Z0-9])" % (
            "|".join(keys))
        self.re_code = re.compile(regexp_string, re.IGNORECASE)

        # remove "-eng" including the hyphen but not -fr from fr-fr
        keys = [key for key in keys if '-' not in key and '_' not in key]
        regexp_string = "[-_](?:%s)(?![a-zA-Z0-9])" % (
            "|".join(keys))
        self.re_strip = re.compile(regexp_string, re.IGNORECASE)

    def strip_path(self, path):
        components = []
        for c in path.split('/'):
            c = self.re_strip.sub('', c)
            components.append(self.re_code.sub('', c))
        return '/'.join(components)

    def strip_query(self, query):
        result = []
        for k, v in urlparse.parse_qsl(query, keep_blank_values=True):
            v = self.re_code.sub('', v)
            result.append((k, v))
        return urllib.urlencode(result)

    def stripn(self, uri):
        return self.re_code.subn('', uri)

    def strip(self, uri):
        return self.re_code.sub('', uri)

    def match(self, uri):
        for match in self.re_code.findall(uri):
            match = match.lower()
            assert match in self.code_to_language, \
                "Unknown match: %s\n" % match
            return self.code_to_language[match]
        return ""


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

    args = parser.parse_args(sys.argv[1:])

    candidates = {}
    if args.candidates:
        candidates = read_candidates(args.candidates)

    language_stripper = LanguageStripper(languages=[args.lang])

    for line in sys.stdin:
        k, v = line.split("\t")
        languages = json.loads(v)['languages']

        if args.lang not in [l for l, b in languages]:
            # this page does not have text in the language
            # we're looking for
            continue

        tld, uri, crawl = k.split(' ')

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
        stripped_path = re.sub(r'--+', '-', stripped_path)

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

        # remove new trailing /
        if stripped_uri and stripped_uri[-1] == '/' \
                and parsed_uri.path and parsed_uri.path[-1] != '/':
            stripped_uri = stripped_uri[:-1]

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

#!/usr/bin/env python
# -*- coding: utf-8 -*-
import urllib
import re
import urlparse


class LanguageStripper(object):

    def __init__(self, languages=None, strip_query_variables=False):
        self._strip_query_variables = []
        if strip_query_variables:
            self._strip_query_variables = [
                'lang', 'clang', 'language', 'locale', 'selectedLocale']
        self.code_to_language = {}
        # These should all be lower-case, matching is case-insensitive
        for code in ['arabic', 'ara', 'ar']:
            self.code_to_language[code] = 'ar'
        for code in ['bulgarian', 'bul', 'bg']:
            self.code_to_language[code] = 'bg'
        for code in ['czech', 'cze', 'cz', 'cs']:
            self.code_to_language[code] = 'cs'
        for code in ['deutsch', 'german', 'ger', 'deu', 'de']:
            self.code_to_language[code] = 'de'
        for code in ['english', 'eng', 'en']:
            self.code_to_language[code] = 'en'
        for code in ['espanol', 'spanish', 'spa', 'esp', 'es']:
            self.code_to_language[code] = 'es'
        for code in ['french', 'francais', 'fran', 'fra', 'fre', 'fr']:
            self.code_to_language[code] = 'fr'
        for code in ['chinese', 'chi', 'zh']:
            self.code_to_language[code] = 'zh'
        # new, not in 'Dirt-Cheap'-paper
        for code in ['tedesco', 'de-de', 'de-ch', 'de-at', 'de-li', 'de-lu',
                     'allemand']:
            self.code_to_language[code] = 'de'
        for code in ['fr-be', 'fr-ca', 'fr-fr', 'fr-lu', 'fr-ch', 'f']:
            self.code_to_language[code] = 'fr'
        for code in ['italian', 'italiano', 'ital', 'ita', 'it-it', 'it-ch',
                     'it']:
            self.code_to_language[code] = 'it'
        for code in ['en-en', 'en-us', 'en-uk', 'en-ca', 'en-bz', 'en-ab',
                     'en-in', 'en-ie', 'en-jm', 'en-nz', 'en-ph', 'en-za',
                     'en-tt', 'gb', 'en-gb', 'inglese', 'englisch', 'us', 'e']:
            self.code_to_language[code] = 'en'
        for code in ['romanian', 'romana', 'romlang', 'rom', 'ro-ro', 'ro']:
            self.code_to_language[code] = 'ro'
        for code in ['soma', 'som', 'so', 'somal', 'somali', 'so-so',
                     'af-soomaali', 'soomaali']:
            self.code_to_language[code] = 'so'
        for code in ['turkish', 'tur', 'turkic', 'tr-tr', 'tr']:
            self.code_to_language[code] = 'tr'
        for code in ['finnish', 'finnisch', 'fin', 'suomi', 'suomeksi',
                     'suominen', 'suomija', 'fi-fi', 'fi']:
            self.code_to_language[code] = 'fi'

        if languages is not None:
            kv_pairs = [(k, v) for k, v in self.code_to_language.items()
                        if v in languages]
            self.code_to_language = dict(kv_pairs)

        for code, lang in self.code_to_language.items():
            # add de_de from de-de
            self.code_to_language[code.replace('-', '_')] = lang

        keys = self.code_to_language.keys()
        keys.sort(key=len, reverse=True)
        regexp_string = '(?<![a-zA-Z0-9])(?:%s)(?![a-zA-Z0-9])' % (
            '|'.join(keys))
        self.re_code = re.compile(regexp_string, re.IGNORECASE)

        # remove '-eng' including the hyphen but not -fr from fr-fr
        keys = [key for key in keys if '-' not in key and '_' not in key]
        regexp_string = '[-_](?:%s)(?![a-zA-Z0-9])' % (
            '|'.join(keys))
        self.re_strip = re.compile(regexp_string, re.IGNORECASE)

        self.re_punct_at_start = re.compile(r'^[^a-zA-Z0-9]+')
        self.re_punct_at_end = re.compile(r'[^a-zA-Z0-9]+$')

    def strip_path(self, path):
        components = []
        for c in path.split('/'):
            stripped = self.re_strip.sub('', c)
            stripped = self.re_code.sub('', stripped)
            if stripped:
                if not self.re_punct_at_start.match(c) and \
                        self.re_punct_at_start.match(stripped):
                    stripped = self.re_punct_at_start.sub('', stripped)
            if stripped:
                if not self.re_punct_at_end.match(c) and \
                        self.re_punct_at_end.match(stripped):
                    stripped = self.re_punct_at_end.sub('', stripped)
            if stripped:
                components.append(stripped)
        return '/'.join(components)

    def strip_query(self, query):
        result = []
        for k, v in urlparse.parse_qsl(query, keep_blank_values=True):

            k_lower = k.lower()
            ignore = False
            for v in self._strip_query_variables:
                if v.endswith(k_lower) or v.startswith(k_lower):
                    ignore = True
            if ignore:
                continue

            stripped_k = self.re_code.sub('', k)
            if not stripped_k:
                continue
            stripped_v = self.re_code.sub('', v)
            if stripped_v == v or stripped_v:
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
                'Unknown match: %s\n' % match
            return self.code_to_language[match]
        return ''

    def strip_uri(self, uri, expected_language=None,
                  remove_index=False):
        ''' Returns (stripped_uri, success) '''
        parsed_uri = urlparse.urlparse(uri)

        matched_languages = [self.match(parsed_uri.path),
                             self.match(parsed_uri.query)]

        if (expected_language is not None) and \
                (expected_language not in matched_languages):
            # we removed a bit of the URL but is does not support our
            # hope to find expected_language, e.g. removed /fr/ when we were
            # looking for Italian pages.
            return '', False

        stripped_path = self.strip_path(parsed_uri.path)

        # repair some stripping artifacts
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

        stripped_query = self.strip_query(parsed_uri.query)

        # remove index files from tail of path if query empty
        if remove_index and not stripped_query:
            if stripped_path.split('/')[-1].startswith('index'):
                stripped_path = '/'.join(stripped_path.split('/')[:-1]) + '/'

        netloc = parsed_uri.netloc
        if '@' in netloc:
            netloc = netloc.split('@')[1]
        if ':' in netloc:
            netloc = netloc.split(':')[0]
        if not netloc:
            return '', False

        stripped_uri = urlparse.ParseResult(scheme='http',
                                            netloc=parsed_uri.netloc,
                                            path=stripped_path,
                                            params='',
                                            query=stripped_query,
                                            fragment='').geturl()

        return stripped_uri, True


if __name__ == '__main__':
    import argparse
    import sys
    parser = argparse.ArgumentParser()
    parser.add_argument('-languages', help='language codes', nargs='+')
    args = parser.parse_args()

    language_stripper = LanguageStripper(languages=args.languages)

    for line in sys.stdin:
        stripped = []
        changed = False
        for uri in line.strip().split('\t'):
            stripped_uri, success = language_stripper.strip_uri(uri)
            if success:
                stripped.append(stripped_uri)
                if stripped_uri != uri:
                    changed = True

        if changed:
            print line.strip(), '\t'.join(stripped)

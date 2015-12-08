#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from bs4 import UnicodeDammit
import chared.detector
import unicodedata
import cld2


"""
Util to convert everything to Unicode
"""


class TextSanitizer():

    @staticmethod
    def _sanitize(c):
        """ Returns space if character is not printable """
        category = unicodedata.category(c)[0]
        if category == 'C':  # remove control characters
            return u' '
        if category == 'Z':  # replace all spaces by normal ones
            return u' '
        return c

    @staticmethod
    def clean_utf8(s):
        """ Removes most funny characters from Unicode """
        assert isinstance(s, unicode)
        s = unicodedata.normalize('NFC', s)
        sanitized_lines = []
        for line in s.split(u"\n"):
            sanitized_lines.append(u"".join(map(TextSanitizer._sanitize,
                                                line)))
        return u"\n".join(sanitized_lines)


def _guess_lang_from_data(data, is_html, default_lang='en'):
    assert isinstance(data, unicode)
    data = TextSanitizer.clean_utf8(data)
    # data = data.encode('utf-8', 'ignore').decode('utf-8', 'ignore')
    # print "broken", data.encode("utf-8")[17929 - 17933]

    reliable, text_bytes, detected_languages = cld2.detect(
        data.encode('utf-8', 'ignore'), isPlainText=(not is_html),
        useFullLangTables=True, bestEffort=True)
    if not reliable:
        return default_lang
    else:
        return detected_languages[0][1]


def _to_unicode_chared(data, lang='en', verbose=False):
    lang2name = {
        'en': 'english',
        'de': 'german',
        'fr': 'french',
        'it': 'italian'}
    assert lang in lang2name, "unknown language: %s\n" % lang
    model_path = chared.detector.get_model_path(lang2name[lang])
    model = chared.detector.EncodingDetector.load(model_path)
    encodings = model.classify(data)
    if verbose:
        sys.stderr.write("Chared Encoding: %s\n" % (str(encodings)))
    for enc in encodings:
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            pass
    sys.stderr.write("Falling back to %s + ignore\n" % (encodings[0]))
    return data.decode(encodings[0], 'ignore')


def to_unicode(data, is_html=False, detwingle=False, verbose=True,
               lang=None):
    " converts everything to unicode"
    dammit = UnicodeDammit(data, is_html=is_html)
    if detwingle and dammit.original_encoding == 'windows-1252':
        new_data = UnicodeDammit.detwingle(data)
        dammit = UnicodeDammit(new_data, is_html=is_html)

    if verbose:
        sys.stderr.write("Original encoding (via BS): %s\n" %
                         (dammit.original_encoding))

    if lang is None:
        return dammit.unicode_markup

    if lang == 'auto':
        lang = _guess_lang_from_data(dammit.unicode_markup, is_html=is_html)
        if verbose:
            sys.stderr.write("Detected language: %s\n" % (lang))

    return _to_unicode_chared(data, lang, verbose=verbose)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-infile', type=argparse.FileType('w'),
                        help='output file', default=sys.stdin)
    parser.add_argument('-outfile', type=argparse.FileType('w'),
                        help='output file', default=sys.stdout)
    parser.add_argument('-html', action='store_true',
                        help='input is HTML')
    parser.add_argument('-language',
                        help='Language hint for chared. Use "auto" if unknown')
    parser.add_argument('-detwingle', action='store_true',
                        help='fix mixed UTF-8 and windows-1252 encodings')
    args = parser.parse_args()

    data = args.infile.read()
    unicode_data = to_unicode(data, is_html=args.html,
                              detwingle=args.detwingle, verbose=True,
                              lang=args.language)
    args.outfile.write(unicode_data.encode('utf-8'))

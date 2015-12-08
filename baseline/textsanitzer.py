#!/usr/bin/env python
# -*- coding: utf-8 -*-

from bs4 import UnicodeDammit
import chared.detector
import cld2
import re
import sys
import unicodedata


""" Utility functions to reliably read text with
    unknown or broken encoding and return proper
    unicode.
"""


class TextSanitizer():

    @staticmethod
    def clean_whitespace(s, linesep=u'\n'):
        """ Cleans empty lines and repeated whitespace """
        # remove empty lines
        assert isinstance(s, unicode)
        s = s.replace('\r\n', '\n')
        s = [l.strip() for l in s.split(u'\n') if l.strip()]
        return linesep.join(re.sub("\s+", " ", l) for l in s)

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

    @staticmethod
    def guess_lang_from_data(data, is_html, default_lang='en'):
        assert isinstance(data, unicode)
        data = TextSanitizer.clean_utf8(data)  # cld2 needs clean input
        reliable, text_bytes, detected_languages = cld2.detect(
            data.encode('utf-8', 'ignore'), isPlainText=(not is_html),
            useFullLangTables=True, bestEffort=True)
        if not reliable:
            return default_lang
        else:
            return detected_languages[0][1]

    @staticmethod
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

        # try all detected encodings
        for enc in encodings:
            try:
                return data.decode(enc)
            except UnicodeDecodeError:
                pass
        sys.stderr.write("Falling back to %s + ignore\n" % (encodings[0]))
        return data.decode(encodings[0], 'ignore')

    @staticmethod
    def to_unicode(data, is_html=False, detwingle=False, verbose=False,
                   lang=None):
        """ Produce unicode from text of unknown encoding.
        Input: bytestring """
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
            lang = TextSanitizer.guess_lang_from_data(
                dammit.unicode_markup, is_html=is_html)
            if verbose:
                sys.stderr.write("Detected language: %s\n" % (lang))

        return TextSanitizer._to_unicode_chared(data, lang, verbose=verbose)

    @staticmethod
    def clean_text(text, sanitize=True, clean_whitespace=True):
        """ Input: unicode string,
            Output: sanitized & cleaned unicode string """
        assert isinstance(text, unicode)
        if sanitize:
            text = TextSanitizer.clean_utf8(text)
        if clean_whitespace:
            text = TextSanitizer.clean_whitespace(text)
        assert isinstance(text, unicode)
        return text

    @staticmethod
    def read_text(filehandle, sanitize=True, clean_whitespace=True):
        """ Read from filehandle and use best-effort decoding/cleaning """
        text = filehandle.read()
        if not text:
            return u''
        text = TextSanitizer.to_unicode(text)
        text = TextSanitizer.clean_text(text, sanitize, clean_whitespace)
        assert isinstance(text, unicode)
        return text

    @staticmethod
    def read_file(filename, sanitize=True, clean_whitespace=True):
        """ Read a file and use best-effort decoding/cleaning """
        try:
            f = open(filename, 'r')
            return TextSanitizer.read_text(f, sanitize, clean_whitespace)
        except IOError:
            sys.stderr.write("Cannot read file: %s\n" % filename)
            return u""

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
    unicode_data = TextSanitizer.to_unicode(data, is_html=args.html,
                                            detwingle=args.detwingle,
                                            verbose=True,
                                            lang=args.language)
    args.outfile.write(unicode_data.encode('utf-8'))

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import sys
import unicodedata
from util import encoding

""" Utility functions to reliably read text with
    unknown of broken encoding and return proper
    unicode.
"""


class TextSanitizer():

    @staticmethod
    def clean_whitespace(s):
        """ Cleans empty lines and repeated whitespace """
        # remove empty lines
        assert isinstance(s, unicode)
        s = [l.strip() for l in s.split(u"\n") if l.strip()]
        return u"\n".join(re.sub("\s+", " ", l) for l in s)

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
    def to_unicode(text):
        """ Produce unicode from text of unknown encoding.
        Input: bytestring """
        return encoding.to_unicode(text)

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

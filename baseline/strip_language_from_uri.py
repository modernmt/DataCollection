#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import re
import urlparse

magic_number = "df6fa1abb58549287111ba8d776733e9"


def stoi(s):
    """ works like int(s) but also accepts floats and scientific notation """
    try:
        return int(s)
    except ValueError:
        return int(float(s))


class LanguageStripper(object):

    def __init__(self):
        self.code_to_language = {}
        for code in ["arabic", "ara", "ar"]:
            self.code_to_language[code] = "ARABIC"
        for code in ["bulgarian", "bul", "bg"]:
            self.code_to_language[code] = "BULGARIAN"
        for code in ["czech", "cze", "cz", "cs"]:
            self.code_to_language[code] = "CZECH"
        for code in ["deutsch", "german", "ger", "deu", "de"]:
            self.code_to_language[code] = "GERMAN"
        for code in ["english", "eng", "en"]:
            self.code_to_language[code] = "ENGLISH"
        for code in ["espanol", "spanish", "spa", "esp", "es"]:
            self.code_to_language[code] = "SPANISH"
        for code in ["french", "francais", "fra", "fre", "fr"]:
            self.code_to_language[code] = "FRENCH"
        for code in ["chinese", "chi", "zh"]:
            self.code_to_language[code] = "CHINESE"
        regexp_string = "(?<![a-zA-Z0-9])(?:%s)(?![a-zA-Z0-9])" % (
            "|".join(self.code_to_language.keys()))
        self.re_code = re.compile(regexp_string)

    def stripn(self, uri):
        return self.re_code.subn('', uri)

    def strip(self, uri):
        return self.re_code.sub('', uri)

    def match(self, uri):
        for match in self.re_code.findall(uri):
            assert match in self.code_to_language
            return self.code_to_language[match]
        return ""


def get_languages(buffer):
    return [(lang, int(percentage), stoi(num_bytes))
            for lang, percentage, num_bytes in
            [line.split() for line in buffer]]


def process_buffer(buffer, language_stripper):
    if not buffer or len(buffer) < 2:
        return
    assert buffer[0].startswith(magic_number)

    uri = buffer[0].split(' ', 2)[1].split(':', 1)[1]
    parsed_uri = urlparse.urlparse(uri)

    matched_language = language_stripper.match(parsed_uri.path)
    if not matched_language:
        matched_language = language_stripper.match(parsed_uri.query)
        if not matched_language:
            return

    stripped_path = language_stripper.strip(parsed_uri.path)
    stripped_query = language_stripper.strip(parsed_uri.query)
    stripped_uri = urlparse.ParseResult(parsed_uri.scheme,
                                        parsed_uri.netloc,
                                        stripped_path,
                                        parsed_uri.params,
                                        stripped_query,
                                        parsed_uri.fragment).geturl()

    languages = [lang for lang, percent, num_bytes in
                 get_languages(buffer[1:])]
    print "\t".join((stripped_uri, uri, matched_language, "/".join(languages))).encode('utf-8')


if __name__ == "__main__":
    buffer = []
    language_stripper = LanguageStripper()
    for line in sys.stdin:
        line = line.decode("utf-8", "ignore")
        if line.startswith(magic_number):
            process_buffer(buffer, language_stripper)
            buffer = [line]
        elif buffer:
            buffer.append(line)
    process_buffer(buffer, language_stripper)

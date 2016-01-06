#!/usr/bin/env python
# -*- coding: utf-8 -*-
import base64
import langid
import re
import sys

from html2text import html2text
from textsanitzer import TextSanitizer
from external_processor import ExternalTextProcessor

magic_numer = "df6fa1abb58549287111ba8d776733e9"

timeout = 10.0


def original_url(html):
    m = re.search(r"<!-- Mirrored from ([^>]+) by HTTrack Website Copier",
                  html)
    if m is None:
        return "unknown_url"
    return m.groups()[0]


def langsplit(uri, langsplit_exec, text):
    cmd = [langsplit_exec, "--printchunks"]
    proc = ExternalTextProcessor(cmd)
    tld = uri.split("/")[0].split(".")[-1]
    header = u"%s tld:%s uri:%s\n" % (magic_numer, tld, uri)
    output = proc.process(u"\n".join([header, text]))

    if not output.strip():
        res = langid.classify(text)
        lang = res[0]
        header = "%s\tlanguage:%s\tbytes:%d\n" % (header.rstrip(),
                                                  lang,
                                                  len(text.encode("utf-8")))
        return header + text
    return output


def extract_language(langsplit_output, expected_lang):
    text = []
    l = None  # language of current span
    for line in langsplit_output.split("\n"):
        # df6fa1abb58549287111ba8d776733e9 tld:www
        # uri:www.hettahuskies.com/doghotel/hotel.html language:en offset:0
        # bytes: 3853

        if not line.strip():
            continue

        if not line.startswith(magic_numer):
            assert l is not None
            if l == expected_lang:
                text.append(line)
        else:
            for kv in line.split():
                if kv.startswith("language:"):
                    l = kv.split(":", 1)[1]

    return u'\n'.join(text)


def split_sentences(text, sentence_splitter_cmd, lang):
    if not sentence_splitter_cmd:
        return text.split('\n')

    sentences = []
    proc = ExternalTextProcessor([sentence_splitter_cmd, "-l", lang])
    output = proc.process(text.replace("\n", "\n\n"))

    for line in output.split("\n"):
        line = line.strip()
        if not line or line == "<P>":
            continue
        sentences.append(line)

    return sentences


def tokenize(text, tokenizer_cmd, lang):
    proc = ExternalTextProcessor([tokenizer_cmd, "-a", "-l", lang])
    output = proc.process(text.strip())
    return output


def normalize(text, normalizer_cmd, lang):
    proc = ExternalTextProcessor([normalizer_cmd, lang])
    output = proc.process(text.strip())
    return output

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    # parser.add_argument('-filename', type=argparse.FileType('w'),
    #                     help='filename without prefix', required=True)
    parser.add_argument('-outfile', type=argparse.FileType('w'),
                        help='output file', required=True)
    # parser.add_argument('-prefix', help='prefix added to make filenames',
    #                     default="/fs/syn0/pkoehn/crawl/data/site-crawls")
    parser.add_argument('-lang', help='non-english language', default='fr')
    parser.add_argument(
        '-splitter', help='moses sentence splitting script',
        default="/home/buck/net/build/moses-clean/scripts/ems/support/split-sentences.perl")
    parser.add_argument(
        '-normalizer', help='moses normalization script',
        default="/home/buck/net/build/moses-clean/scripts/tokenizer/normalize-punctuation.perl")
    parser.add_argument(
        '-tokenizer', help='moses tokenization script',
        default="/home/buck/net/build/moses-clean/scripts/tokenizer/tokenizer.perl")
    parser.add_argument('-langsplit', help='langsplit executable',
                        default="/home/buck/net/build/mtma_bitext/html_convert/langsplit")
    parser.add_argument(
        '-fromhtml', help='re-extract text from HTML', action='store_true')

    args = parser.parse_args(sys.argv[1:])

    for line in sys.stdin:
        lang, mime_type, enc, uri, html, text = line.split("\t")
        uri = TextSanitizer.to_unicode(uri)

        if args.fromhtml:
            text = html2text(base64.b64decode(html), sanitize=True,
                             ignore_br=False)
        else:
            text = base64.b64decode(text).decode("utf-8")

        if not text.strip():
            sys.stderr.write("no text found in %s\n" % uri)
            continue

        langsplit_output = langsplit(uri, args.langsplit, text)
        # print langsplit_output.encode("utf-8")
        # sys.exit()
        # langsplit_output.decode("utf-8")

        foreign_text = extract_language(langsplit_output, args.lang)
        # print foreign_text.encode("utf-8")
        # sys.exit()
        foreign_text = TextSanitizer.clean_text(foreign_text)
        # print foreign_text.encode("utf-8")
        # sys.exit()

        if not foreign_text:
            # sys.stderr.write("no '%s' text found in %s\n" %
            #                  (args.lang, uri))
            continue

        for foreign_line in split_sentences(foreign_text,
                                            args.splitter,
                                            args.lang):
            # Todo: Sentence splitting here.
            if args.normalizer:
                foreign_line = normalize(
                    foreign_line, args.normalizer, args.lang)
            if args.tokenizer:
                foreign_line = tokenize(
                    foreign_line, args.tokenizer, args.lang)
            if not foreign_line.strip():
                continue
            args.outfile.write("%s\t%s\n"
                               % (uri.encode("utf-8"),
                                  foreign_line.strip().encode("utf-8")))

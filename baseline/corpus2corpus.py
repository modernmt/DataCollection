#!/usr/bin/env python
# -*- coding: utf-8 -*-
import base64
import sys

from html2text import html2text
from external_processor import TextProcessor


def process_candidates(candidates, outfile):
    if candidates[0][-1] == "" or candidates[1][-1] == "":
        return
    src_url, src_text, src_html = candidates[0]
    tgt_url, tgt_text, tgt_html = candidates[1]


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-outfile', type=argparse.FileType('w'),
                        help='output file', default=sys.stdout)
    parser.add_argument('-source_tokenizer',
                        help='call to source tokenizer, incl. args')
    parser.add_argument('-source_splitter',
                        help='call to source sentence splitter, incl. args')
    parser.add_argument('-target_tokenizer',
                        help='call to target tokenizer, incl. args')
    parser.add_argument('-target_splitter',
                        help='call to target sentence splitter, incl. args')
    args = parser.parse_args()

    source_text_processor = TextProcessor(splitter=args.source_splitter,
                                          tokenizer=args.source_tokenizer)
    target_text_processor = TextProcessor(splitter=args.target_splitter,
                                          tokenizer=args.target_tokenizer)

    for line in sys.stdin:
        src_url, tgt_url, _, _, src_html, tgt_html = line.strip().split("\t")

        src_text = html2text(base64.b64decode(src_html), sanitize=True)
        tgt_text = html2text(base64.b64decode(tgt_html), sanitize=True)
        src_text = source_text_processor.process(unicode(src_text))
        tgt_text = source_text_processor.process(unicode(tgt_text))

        args.outfile.write("\t".join((src_url,
                                      tgt_url,
                                      base64.b64encode(
                                          src_text.encode('utf-8')),
                                      base64.b64encode(
                                          tgt_text.encode('utf-8')),
                                      src_html,
                                      tgt_html)))
        args.outfile.write("\n")

#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import defaultdict
import argparse
import cld2
import langid
import sys
import codecs


""" Removes some wrongly aligned pairs from hunalign output """


class LanguageIdentifier(object):

    def __init__(self, use_cld2, valid_languages=None):
        self.use_cld2 = use_cld2
        self.valid_languages = [l.lower() for l in valid_languages]
        if not use_cld2 and valid_languages:
            langid.set_languages(self.valid_languages)

    def is_language(self, s, expected_lang):
        """ Check if the language of the segment cannot be reliably identified
        as another language. If another than the expected language is
        detected return False """
        expected_lang = expected_lang.lower()
        if self.valid_languages:
            assert expected_lang in self.valid_languages
        if self.use_cld2:
            reliable, _text_bytes, details = cld2.detect(
                s.encode("utf-8"),
                isPlainText=True,
                useFullLangTables=True,
                bestEffort=True)
            if reliable:
                for _lang, langcode, confidence, score in details:
                    if langcode == expected_lang and confidence >= 10:
                        return True
                return False
            else:  # unreliable is still counted as OK
                return True
        else:
            lang, confidence = langid.classify(source.lower())
            if lang != expected_lang and confidence > 0.9:
                # confidence for wrong language higher than 90%
                return False
            else:
                return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('infile', nargs='?', type=argparse.FileType('r'),
                        default=sys.stdin)
    parser.add_argument('outfile', nargs='?', type=argparse.FileType('w'),
                        default=sys.stdout)
    parser.add_argument('-deleted', help='file to keep deleted lines',
                        dest='deleted_filename')
    parser.add_argument('-minscore', type=float, default=0,
                        help='minimum score from hunalign')
    parser.add_argument('-slang', '--lang1', help='source language',
                        dest='source_lang', default='en')
    parser.add_argument('-tlang', '--lang2', help='target language',
                        dest='target_lang', default='fr')
    parser.add_argument('-cld2', help='use CLD2 instead of langid.py',
                        action='store_true')
    args = parser.parse_args()

    n_written = 0
    n_total = 0
    lid = LanguageIdentifier(args.cld2, [args.source_lang, args.target_lang])
    if args.deleted_filename:
	deleted_file = codecs.open(args.deleted_filename,'w',encoding='utf-8')
    for line in args.infile:
        n_total += 1
        score = 1.0
	srcurl = ""
	tgturl = ""
        split_line = line.rstrip('\n').split("\t")
	if len(split_line) <= 1:
	    deleted_file.write("line_short\t%s\n" % line)
	    continue
	if len(split_line) > 5:
	    deleted_file.write("line_long\t%s\n" % line)
	    continue
        if len(split_line) == 5:
            srcurl, tgturl, source, target, score = split_line
        if len(split_line) == 4:
            srcurl, tgturl, source, target = split_line
        if len(split_line) == 3:
            source, target, score = split_line
        if len(split_line) == 2:
            source, target = split_line
        source = source.decode('utf-8', 'ignore')
        target = target.decode('utf-8', 'ignore')

        if source == target:
	    deleted_file.write("identical\t%s\n" % target)
            continue
        if not source.strip():
	    deleted_file.write("source_empty\n")
            continue
        elif not target.strip():
	    deleted_file.write("target_empty\n")
            continue
        if float(score) < args.minscore:
	    deleted_file.write("low_score\t%s\t%s\t%s\n" % (source,target,score))
            continue

        if float((len(source) + 15)) / float(len(target) + 15) > 1.5:
	    deleted_file.write("source_too_long\t%s\t%s\n" % (source,target))
            continue
	# To be debugged - criterion is exactly like previous, so never reached
        if float((len(target) + 15)) / float(len(source) + 15) > 1.5:
	    deleted_file.write("source_too_short\t%s\t%s\n" % (source,target))
            continue

        if not lid.is_language(source, args.source_lang):
	    deleted_file.write("source_lang\t%s\n" % source)
            continue
        if not lid.is_language(target, args.target_lang):
	    deleted_file.write("target_lang\t%s\n" % target)
            continue

        args.outfile.write(line)
        n_written += 1

    if args.deleted_filename:
        deleted_file.write("Written: %d of %d = %f percent\n" %
                           (n_written, n_total,
                            100. * n_written / max((1, n_total))))

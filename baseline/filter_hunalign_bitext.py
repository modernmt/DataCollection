#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import defaultdict
import argparse
import cld2
import langid
import sys


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
                        type=argparse.FileType('w'))
    parser.add_argument('-minscore', type=float, default=0,
                        help='minimum score from hunalign')
    parser.add_argument('-slang', '--lang1', help='source language',
                        dest='source_lang', default='en')
    parser.add_argument('-tlang', '--lang2', help='target language',
                        dest='target_lang', default='fr')
    parser.add_argument('-cld2', help='use CLD2 instead of langid.py',
                        action='store_true')
    args = parser.parse_args()

    deletions = defaultdict(list)

    n_written = 0
    n_total = 0
    lid = LanguageIdentifier(args.cld2, [args.source_lang, args.target_lang])
    for line in args.infile:
        n_total += 1
        score = 1.0
        split_line = line.rstrip('\n').split("\t")
        if len(split_line) == 5:
            split_line = split_line[-3:]
        if len(split_line) == 3:
            source, target, score = split_line
        else:
            assert len(split_line) == 2
            source, target = split_line
        source = source.decode('utf-8', 'ignore')
        target = target.decode('utf-8', 'ignore')

        if source == target:
            deletions["identical"].append(target)
            continue
        if not source.strip():
            deletions["source_empty"].append('')
            continue
        elif not target.strip():
            deletions["target_empty"].append('')
            continue
        if float(score) < args.minscore:
            deletions["low score"].append("\t".join((source, target, score)))
            continue

        if float((len(source) + 15)) / float(len(target) + 15) > 1.5:
            deletions["source_too_long"].append("%s\t%s" % (source, target))
            continue
        if float((len(target) + 15)) / float(len(source) + 15) > 1.5:
            deletions["source_too_short"].append("%s\t%s" % (source, target))
            continue

        if not lid.is_language(source, args.source_lang):
            deletions["source_lang"].append(source)
            continue
        if not lid.is_language(target, args.target_lang):
            deletions["target_lang"].append(target)
            continue

        args.outfile.write(line)
        n_written += 1

    if args.deleted:
        args.deleted.write("Written: %d of %d = %f percent\n" %
                           (n_written, n_total,
                            100. * n_written / max((1, n_total))))
        for reason, deleted in deletions.iteritems():
            args.deleted.write("Deleted %d items due to %s\n"
                               % (len(deleted), reason))
            for line in deleted:
                if line.strip():
                    args.deleted.write("\t%s\n" % line.encode('utf-8'))

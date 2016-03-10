#!/usr/bin/env python

import sys
import base64
from collections import defaultdict
import codecs

from bitextorutil import read_lett
sys.path.append('/home/buck/net/build/bitextor/share/bitextor/utils')
from unicodepunct import get_unicode_punct
from nltk import word_tokenize

punctuation_chars = get_unicode_punct()


def collect_vocab(filename, lang):
    vocab = set()
    for docid, words in read_lett(filename, lang):
        for w in words:
            vocab.add(w)
    return vocab


def read_dictionary(filename, lang1, lang2):
    d = defaultdict(set)
    swap = False  # switch columns in dict file
    with codecs.open(filename, 'r', 'utf-8', 'ignore') as dict_file:
        l1, l2 = dict_file.readline().strip().lower().split('\t')
        if l2 == lang1 and l1 == lang2:
            swap = True
        else:
            assert l1 == lang1 and l2 == lang2, \
                "unexpected language pair: %s-%s\n" % (l1, l2)

        for line in dict_file:
            try:
                w1, w2 = line.strip().split('\t')
            except ValueError:
                sys.stderr.write(
                    "Cannot parse dictionary entry: %s\n" % repr(line))
                continue
            if swap:
                w1, w2 = w2, w1
            d[w2].add(w1)   # We're translating lang2 -> lang1
    sys.stderr.write("Read dictionary of %d %s words\n" % (len(d), lang2))
    return d


def extend_dictionary(dictionary, voc1, voc2, quiet=False):
    n_added = 0
    for w in voc1.intersection(voc2):
        if w not in dictionary[w]:
            n_added += 1
            dictionary[w].add(w)
    if not quiet:
        sys.stderr.write("Added %d 1-1 translations\n" % (n_added))
        sys.stderr.write("Final dictionary size: %d\n" % (len(dictionary)))
    return dictionary


def translate_tokens(tokens, d):
    """ Produce set of translated tokens, returns number of tokens that
    were translated. All possible translations of a token are added. """
    n_translated = 0
    translated = set()
    for w in tokens:
        if w not in d:
            continue
        translated.update(d[w])
        n_translated += 1
    return n_translated, translated


def read_counts(filename, lang1, lang2):
    s_counts, t_counts = {}, {}
    for line in open(filename):
        lang, count, w = line.strip().split('\t')
        w = w.decode('utf-8')
        if lang == lang1:
            s_counts[w] = int(count)
        elif lang == lang2:
            t_counts[w] = int(count)
    return s_counts, t_counts


def read_valid_words(filename, lang, max_count):
    v = None
    if filename:
        v = set()
        for line in open(filename):
            lang, count, word = line.split("\t")
            if lang != lang:
                continue
            if max_count > 0 and count > max_count:
                continue
            v.add(word.decode('utf-8'))
        sys.std.write("Limiting to %d valid words in lang %s\n"
                      % (len(v), lang))
    return v


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('lett', help='bitextor lett file')
    parser.add_argument('counts',
                        help='word counts in format lang<tab>word<tab>count')
    parser.add_argument('-lang1',
                        help='Two letter source language code', required=True)
    parser.add_argument('-lang2',
                        help='Two letter target language code', required=True)
    parser.add_argument('-dictionary',
                        help='Dictionary to translate from lang2 to lang1')
    parser.add_argument('-m', help='Max number of occurences to keep word',
                        type=int, default=-1)

    args = parser.parse_args(sys.argv[1:])
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout)

    dictionary = None
    expected_language = args.lang1

    s_counts, t_counts = read_counts(args.counts, args.lang1, args.lang2)
    sys.stderr.write("Read counts for %d %s and %d %s words.\n"
                     % (len(s_counts), args.lang1,
                        len(t_counts), args.lang2))

    if args.dictionary:
        dictionary = read_dictionary(args.dictionary, args.lang1, args.lang2)
        dictionary = extend_dictionary(dictionary,
                                       set(s_counts.keys()),
                                       set(t_counts.keys()))
        expected_language = args.lang2

    sys.stderr.write("Ignoring all languages but '%s'\n" % expected_language)

    valid_words = None
    if expected_language == args.lang1:
        valid_words = set(s_counts.keys())
    else:
        assert expected_language == args.lang2
        valid_words = set(t_counts.keys())

    for doc_id, lang, words in read_lett(args.lett,
                                         expected_language,
                                         as_set=True):
        assert lang == expected_language
        # remove words with too high count
        words.intersection_update(valid_words)

        if dictionary:
            n_original_tokens = len(words)
            n_translated, words = translate_tokens(words, dictionary)
            sys.stdout.write("%d\t%d\t%d\t%s\n" %
                             (doc_id,
                              n_translated,
                              n_original_tokens,
                              u"\t".join(words)))
        else:
            sys.stdout.write("%d\t%s\n" % (doc_id, u"\t".join(words)))

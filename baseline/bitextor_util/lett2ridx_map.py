#!/usr/bin/env python

import sys
import base64
from collections import defaultdict
import codecs

sys.path.append('/home/buck/net/build/bitextor/share/bitextor/utils')
from unicodepunct import get_unicode_punct
from nltk import word_tokenize

punctuation_chars = get_unicode_punct()


def get_tokens(untokenized_text):
    text = " ".join(word_tokenize(untokenized_text))
    token_set = set(text.lower().split())
    # remove tokens that only contain punctuation
    token_set = [w.strip(punctuation_chars) for w in token_set]
    token_set = [w for w in token_set if w]
    return set(token_set)


def read_lett(filename, lang=None):
    # with codecs.open(filename, 'r', 'utf-8') as lettfile:
    with open(filename, 'r') as lettfile:
        for linenr, line in enumerate(lettfile):
            fields = line.strip().split("\t")
            if lang is not None and lang != fields[0]:
                continue
            text = base64.b64decode(fields[5]).decode('utf-8')
            if text.strip():
                words = get_tokens(text)
                yield linenr, words


def collect_vocab(filename, lang):
    vocab = set()
    for docid, words in read_lett(filename, lang):
        for w in words:
            vocab.add(w)
    return vocab


def read_dictionary(filename, lang1, lang2):
    d = defaultdict(list)
    swap = False  # switch columns in dict file
    with codecs.open(filename, 'r', 'utf-8') as dict_file:
        l1, l2 = dict_file.readline().strip().lower().split('\t')
        if l2 == lang1 and l1 == lang2:
            swap = True
        else:
            assert l1 == lang1 and l2 == lang2, \
                "unexpected language pair: %s-%s\n" % (l1, l2)

        for line in dict_file:
            w1, w2 = line.strip().split('\t')
            if swap:
                w1, w2 = w2, w1
            d[w2].append(w1)   # We're translating lang2 -> lang1
    sys.stderr.write("Read dictionary of %d %s words\n" % (len(d), lang2))
    return d


def extend_dictionary(dictionary, voc1, voc2, quiet=False):
    n_added = 0
    for w in voc1.intersection(voc2):
        if w not in dictionary[w]:
            n_added += 1
            dictionary[w].append(w)
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
        for s_token in d[w]:
            translated.add(s_token)
        n_translated += 1
    return n_translated, translated

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('lett', help='bitextor lett file')
    parser.add_argument(
        '-lang1', help='Two letter source language code', required=True)
    parser.add_argument('-lang2', help='Two letter target language code')
    parser.add_argument(
        '-dictionary', help='Dictionary to translate from lang1 to lang2')

    args = parser.parse_args(sys.argv[1:])
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout)

    dictionary = None
    expected_language = args.lang1
    if args.dictionary:
        assert args.lang2, "Need to specify target language\n"
        dictionary = read_dictionary(args.dictionary, args.lang1, args.lang2)
        source_vocab = collect_vocab(args.lett, args.lang1)
        target_vocab = collect_vocab(args.lett, args.lang2)
        dictionary = extend_dictionary(dictionary, source_vocab, target_vocab)
        expected_language = args.lang2
    sys.stderr.write("Ignoring all languages but '%s'\n" % expected_language)

    for doc_id, words in read_lett(args.lett, expected_language):
        if dictionary:
            n_original_tokens = len(words)
            n_translated, words = translate_tokens(words, dictionary)
            sys.stdout.write("%d\t%d\t%d\t%s\n" %
                             (doc_id,
                              n_translated,
                              n_original_tokens,
                              "\t".join(words)))
        else:
            sys.stdout.write("%d\t%s\n" % (doc_id, "\t".join(words)))

#!/usr/bin/env python

import sys
import base64
from collections import defaultdict
import codecs

sys.path.append('/home/buck/net/build/bitextor/share/bitextor/utils')
from unicodepunct import get_unicode_punct
from nltk import word_tokenize

punctuation_chars = get_unicode_punct()


def get_words(untokenized_text):
    text = " ".join(word_tokenize(untokenized_text))
    words = text.lower().split()
    words = [w.strip(punctuation_chars) for w in words]
    words = [w for w in words if w]
    return words


def read_lett(filename, lang=None, as_set=False):
    # with codecs.open(filename, 'r', 'utf-8') as lettfile:
    with open(filename, 'r') as lettfile:
        for linenr, line in enumerate(lettfile):
            fields = line.strip().split("\t")
            if lang is not None and lang != fields[0]:
                continue
            text = base64.b64decode(fields[5]).decode('utf-8').strip()
            if text:
                words = get_words(text)
                if as_set:
                    words = set(words)
                yield linenr, fields[0], words

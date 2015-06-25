#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from math import log
from collections import defaultdict
import numpy as np
from scipy.spatial import distance
# import scipy as sp


def cos_cdist(matrix, vector):
    """
    Compute the cosine distances between each row of matrix and vector.
    """
    v = vector.reshape(1, -1)
    return distance.cdist(matrix, v, 'cosine').reshape(-1)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('engrams', type=argparse.FileType('r'),
                        help="original English ngrams, \
                        Format: ngram<tab>filename")
    parser.add_argument('tngrams', type=argparse.FileType('r'),
                        help="ngrams from translation (into English). \
                        Format: ngram<tab>filename")

    parser.add_argument('langfile', type=argparse.FileType('r'),
                        help="format: filename<tab>main language")
    # parser.add_argument('-filename', type=argparse.FileType('w'),
    #                     help='filename without prefix', required=True)
    parser.add_argument('-outfile', type=argparse.FileType('w'),
                        help='output file', required=True)
    parser.add_argument('-prefix', help='prefix added to make filenames',
                        default="/fs/syn0/pkoehn/crawl/data/site-crawls")
    parser.add_argument('-slang', help='Source language', default='en')
    parser.add_argument('-tlang', help='Non-english language', default='fr')
    args = parser.parse_args(sys.argv[1:])

    # inverse index
    ngram2doc = defaultdict(set)
    ngram2idx = {}  # ngram to dimension
    doc2ngram = defaultdict(set)  # ignore ngram counts (tf)

    for f in (args.engrams, args.tngrams):
        for line in f:
            ngram, filename = line.strip().split("\t", 1)
            ngram2doc[ngram].add(filename)  # docs identified by filename
            doc2ngram[filename].add(ngram)
            ngram2idx[ngram] = len(ngram2idx)

    # precompute idf scores = log ( |D|/df(ngram) )
    ngram2idf = {}
    ndocs = len(doc2ngram)
    for ngram, docs in ngram2doc.iteritems():
        ngram2idf[ngram] = log(float(ndocs) / len(docs))

    # collect sets of source and target docs based on their main language
    source_docs, target_docs = set(), set()
    for line in args.langfile:
        filename, lang = line.strip().split("\t")
        if filename not in doc2ngram:
            sys.stderr.write("no known ngrams for %s\n" % filename)
            continue
        assert lang in (args.slang, args.tlang),\
            "unexpected language %s\n" % lang
        if lang == args.slang:
            source_docs.add(filename)
        else:
            target_docs.add(filename)

    target_docs = list(target_docs)
    source_docs = list(source_docs)

    # matrix of target document vectors
    target_matrix = np.zeros((len(target_docs), len(ngram2idx)))
    for tidx, td in enumerate(target_docs):
        for ngram in doc2ngram[td]:
            ngram_idx = ngram2idx[ngram]
            target_matrix[tidx, ngram_idx] = ngram2idf[ngram]

    for sd in source_docs:
        v = np.zeros(len(ngram2idx))
        for ngram in doc2ngram[sd]:
            ngram_idx = ngram2idx[ngram]
            v[ngram_idx] = ngram2idf[ngram]

        d = cos_cdist(target_matrix, v)
        # print d
        min_dist = np.min(d)
        if min_dist < 1.:
            best_td = target_docs[np.argmin(d)]
            args.outfile.write("%s\t%s\t%f\n" % (sd, best_td, min_dist))
        else:
            sys.stderr.write("No match found for %s\n" % sd)


#!/usr/bin/env python
# -*- coding: utf-8 -*-

import numpy as np
import sys

# for Hungarian Algorithm
import munkres

sys.path.append("/home/buck/net/build/DataCollection/baseline")
from strip_language_from_uri import LanguageStripper


def get_best_match(source_corpus, target_corpus, scores):
    stripper = LanguageStripper()
    err = 0
    for s_idx, (s_url, s_page) in enumerate(source_corpus.iteritems()):
        max_idx = np.argmax(scores[s_idx])
        t_url = target_corpus.keys()[max_idx]
        success = stripper.strip(t_url) == stripper.strip(s_page.url)
        if not success:
            err += 1
        # sys.stdout.write("%f\t%s\t%s\t%s\n" %
        #                  (scores[s_idx, max_idx], success, s_url, t_url))
    n = min(len(source_corpus), len(target_corpus))
    sys.stderr.write("Correct (greedy): %d out of %d = %f%%\n" %
                     (n - err, n, (1. * n - err) / n))


def get_best_matching(source_corpus, target_corpus, scores):
    stripper = LanguageStripper()
    err = 0

    m = munkres.Munkres()
    cost_matrix = munkres.make_cost_matrix(scores, lambda cost: 1 - cost)
    indexes = m.compute(cost_matrix)

    for row, column in indexes:
        s_url = source_corpus.keys()[row]
        t_url = target_corpus.keys()[column]
        success = stripper.strip(t_url) == stripper.strip(s_url)
        if not success:
            err += 1
        # sys.stdout.write("%f\t%s\t%s\t%s\n" %
        #                  (scores[row, column], success, s_url, t_url))

    n = min(len(source_corpus), len(target_corpus))
    sys.stderr.write("Correct: %d out of %d = %f%%\n" %
                     (n - err, n, (1. * n - err) / n))

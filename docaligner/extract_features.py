#!/usr/bin/env python
# -*- coding: utf-8 -*-
import math
import numpy as np
import sys
from scipy.stats import pearsonr, spearmanr

from htmlprocessor import HTMLSequencer
from lett import Page, read_lett
from scorer import BOWScorer
from scorer import DistanceScorer
from scorer import LinkDistance
from scorer import SimhashDistance
from scorer import NERDistance
from scorer import StructureScorer
from tokenizer import ExternalProcessor, SpaceTokenizer
from matching import get_best_match, get_best_matching
from ratio import ratio, quick_ratio, real_quick_ratio, jaccard

sys.path.append("/home/buck/net/build/DataCollection/baseline")
from strip_language_from_uri import LanguageStripper


def get_nbest(source_corpus, target_corpus, scores, n=10):
    stripper = LanguageStripper()
    err = 0
    n = min(n, len(source_corpus))
    for s_idx, (s_url, s_page) in enumerate(source_corpus.iteritems()):
        best_score_indices = np.argpartition(scores[s_idx], -n)[-n:]
        t_urls = [target_corpus.keys()[idx] for idx in best_score_indices]
        t_urls = map(stripper.strip, t_urls)
        success = stripper.strip(s_page.url) in t_urls
        if not success:
            err += 1
    mlen = min(len(source_corpus), len(target_corpus))
    sys.stderr.write("Correct in %d-best: %d out of %d = %f%%\n" %
                     (n, mlen - err, mlen, (1. * mlen - err) / mlen))


def get_class_value_pairs(source_corpus, target_corpus, scores,
                          ignore=None):
    stripper = LanguageStripper()

    for s_idx, (s_url, s_page) in enumerate(source_corpus.iteritems()):
        for t_idx, (t_url, t_page) in enumerate(target_corpus.iteritems()):
            success = stripper.strip(t_url) == stripper.strip(s_url)
            score = scores[s_idx, t_idx]
            if ignore is not None and ignore(score):
                continue
            yield s_idx, t_idx, int(success), score


def get_ranks(source_corpus, target_corpus, scores):
    stripper = LanguageStripper()

    for s_idx, (s_url, s_page) in enumerate(source_corpus.iteritems()):
        s_url_stripped = stripper.strip(s_url)
        for t_idx, (t_url, t_page) in enumerate(target_corpus.iteritems()):
            if stripper.strip(t_url) == s_url_stripped:
                rank = sorted(scores[s_idx],
                              reverse=True).index(scores[s_idx, t_idx])
                yield rank
                break


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'lettfile', help='input lett file', type=argparse.FileType('r'))
    parser.add_argument(
        '-outfile', help='output file', type=argparse.FileType('w'),
        default=sys.stdout)
    parser.add_argument('feature',
                        choices=['LinkDistance', 'BOW', 'Simhash',
                                 'Structure'])
    parser.add_argument('-ngram_size', help="length of ngram from Simhash",
                        default=2, type=int)
    parser.add_argument('-xpath', help="xpath for LinkDistance",
                        default="//a/@href")
    parser.add_argument('-slang', help='source language', default='en')
    parser.add_argument('-tlang', help='target language', default='fr')
    parser.add_argument(
        '-source_tokenizer', help='call to tokenizer, including arguments')
    parser.add_argument(
        '-target_tokenizer', help='call to tokenizer, including arguments')
    parser.add_argument(
        '-corenlp_service', help='corenlp json service location',
        default='http://localhost:8080')
    args = parser.parse_args(sys.argv[1:])

    source_tokenizer = ExternalProcessor(
        args.source_tokenizer) if args.source_tokenizer else SpaceTokenizer()
    target_tokenizer = ExternalProcessor(
        args.target_tokenizer) if args.target_tokenizer else SpaceTokenizer()

    # read source and target corpus
    s, t = read_lett(args.lettfile, args.slang, args.tlang)

    sys.stderr.write("Read %d %s docs and %d %s docs from %s\n" %
                     (len(s), args.slang,
                      len(t), args.tlang, args.lettfile.name))

    scorer = None
    if args.feature == 'LinkDistance':
        scorer = LinkDistance(xpath=args.xpath, ratio=jaccard)
    elif args.feature == 'BOW':
        scorer = BOWScorer(source_tokenizer=source_tokenizer,
                           target_tokenizer=target_tokenizer)
    elif args.feature == 'Simhash':
        scorer = SimhashDistance(source_tokenizer=source_tokenizer,
                                 target_tokenizer=target_tokenizer,
                                 n=args.ngram_size)
    elif args.feature == 'Structure':
        scorer = StructureScorer(
            length_function=lambda x: len(x.split()),
            growth_function=lambda x: 1 + math.log(x),
            ratio_function=quick_ratio)
    assert scorer is not None, "Need to instantiate scorer first"
    m = scorer.score(s, t)

    # print info
    ranks = list(get_ranks(s, t, m))
    sys.stderr.write("Avg. Rank: %f\n" % (float(sum(ranks)) / len(ranks)))
    n_errors(sum(1 for r in ranks if r > 0))
    print "Err: %d / %d = %f" % (n_errors, len(ranks),
                                 float(n_errors) / len(ranks))
    print sum(1 for r in ranks if r < 20)
    get_nbest(s, t, m, n=20)

    # np.savetxt(args.outfile, m)
    # success, value = [], []
    # for c, v in get_class_value_pairs(s, t, m, ignore=lambda x: x == 0):
    for s_idx, t_idx, c, v in get_class_value_pairs(s, t, m):
        args.outfile.write("%d\tqid:%d\t%f\n" % (c, s_idx, v))
        # args.outfile.write("%d\t%f\n" % (c, v))

    # p_correl, p_val = pearsonr(value, success)
    # sys.stderr.write("%d k/v pairs, %d class 1\n" %
    #                  (len(success), success.count(1)))
    # sys.stderr.write("Pearson:\t%f\tp=%f\n" % (p_correl, p_val))
    #
    # s_correl, p_val = spearmanr(value, success)
    # sys.stderr.write("Spearman:\t%f\tp=%f\n" % (s_correl, p_val))
    #
    # get_best_match(s, t, m)
    # distance_scorers = [LinkDistance(), LinkDistance(xpath="//img/@src")]

    # for length_function in [lambda x: len(x),
    #                         lambda x: len(x.split()),
    #                         lambda x: len(x.split("\n"))][::-1]:
    #     for growth_function in [lambda x: x,
    #                             lambda x: int(math.sqrt(x)),
    #                             lambda x: 1 + int(math.log(x))][::-1]:
    #         for ratio_function in real_quick_ratio, quick_ratio, ratio:
    #             scorer = StructureScorer(
    #                 length_function, growth_function, ratio_function)
    #             m = scorer.score(s, t)
    #             get_best_matching(s, t, m)
    #             get_best_match(s, t, m)

    # distance_scorers = [LinkDistance(),
    #                     SimhashDistance(source_tokenizer=source_tokenizer,
    #                                     target_tokenizer=target_tokenizer,
    #                                     n=1),
    #                     SimhashDistance(source_tokenizer=source_tokenizer,
    #                                     target_tokenizer=target_tokenizer,
    #                                     n=2),
    #                     SimhashDistance(source_tokenizer=source_tokenizer,
    #                                     target_tokenizer=target_tokenizer,
    #                                     n=3),
    #                     SimhashDistance(source_tokenizer=source_tokenizer,
    #                                     target_tokenizer=target_tokenizer,
    #                                     n=4),
    #                     SimhashDistance(source_tokenizer=source_tokenizer,
    #                                     target_tokenizer=target_tokenizer,
    #                                     n=5),
    #                     GaleChurchAlignmentDistance(),
    #                     StructureScorer(
    #                         length_function=lambda x: len(x.split()),
    #                         growth_function=lambda x: 1 + math.log(x),
    #                         ratio_function=lambda x: quick_ratio),
    #                     BOWScorer(source_tokenizer=source_tokenizer,
    #                               target_tokenizer=target_tokenizer),
    #                     LinkDistance(),
    #                     LinkDistance(xpath="//img/@src"),
    #                     NERDistance(args.corenlp_service,
    #                                 source_tokenizer=source_tokenizer,
    #                                 target_tokenizer=target_tokenizer)
    #                     ]

    # distance_scorers = [StructureScorer(
    #     length_function=lambda x: len(x.split()),
    #     growth_function=lambda x: int(1 + math.log(x)),
    #     ratio_function=lambda x: quick_ratio),
    #     BOWScorer(source_tokenizer=source_tokenizer,
    #               target_tokenizer=target_tokenizer),
    #     LinkDistance()]
    # for scorer in distance_scorers:
    #     sys.stderr.write("Running: %s\n" % str(scorer))
    #     m = scorer.score(s, t)
    #     get_best_match(s, t, m)
    #     get_nbest(s, t, m, n=10)
    #     get_nbest(s, t, m, n=20)
    #     get_nbest(s, t, m, n=100)
    # get_best_matching(s, t, m)

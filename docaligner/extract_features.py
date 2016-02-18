#!/usr/bin/env python
# -*- coding: utf-8 -*-
import math
import numpy as np
import sys
import json
from scipy.stats import pearsonr, spearmanr

from htmlprocessor import HTMLSequencer
from lett import Page, read_lett
from scorer import DistanceScorer, GaleChurchScorer
from scorer import WordExtractor, LinkExtractor, StructureExtractor
from scorer import EnglishWordExtractor
from scorer import SimhashDistance
from scorer import NERDistance
from scorer import StructureScorer
from scorer import GaleChurchAlignmentDistance
from scorer import DictionaryScorer
from scorer import CosineDistanceScorer
from tokenizer import ExternalProcessor, SpaceTokenizer, WordPunctTokenizer
from matching import get_best_match, get_best_matching
from ratio import ratio, quick_ratio, real_quick_ratio, jaccard
from ratio import ratio_star, quick_ratio_star
import multiprocessing
import cPickle as pickle

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


def get_ground_truth(source_corpus, target_corpus):
    t = np.zeros((len(source_corpus), len(target_corpus)))
    stripper = LanguageStripper()
    stripped_source_urls = map(stripper.strip, source_corpus.keys())
    stripped_target_urls = map(stripper.strip, target_corpus.keys())

    for s_idx, su in enumerate(stripped_source_urls):
        for t_idx, tu in enumerate(stripped_target_urls):
            if su == tu:
                t[s_idx, t_idx] = 1.0
                break
    sys.stderr.write("Marked %d url pairs\n" % (int(sum(sum(t)))))
    # check 1-1 correspondance
    print "These should be 0:", sum(t.sum(axis=0) > 1), sum(t.sum(axis=1) > 1)
    return t


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


def write_url2dim(source_corpus, target_corpus, fh, file2url):
    f2u = {}
    all_filenames = set(source_corpus.keys())
    all_filenames.update(target_corpus.keys())

    if file2url is not None:
        seen = set()
        for line in file2url:
            filename, url = line.strip().split('\t')
            if not url.startswith("http://"):
                url = "http://" + url
            if filename in all_filenames:
                f2u[filename] = url
                seen.add(filename)

        assert not seen.difference(all_filenames)
        for filename in all_filenames.difference(seen):
            sys.stderr.write("Could not find file %s\n" % filename)

    mapping = {'index_to_source_url': {},
               'index_to_target_url': {},
               'source_url_to_index': {},
               'target_url_to_index': {}}

    for s_idx, su in enumerate(source_corpus.iterkeys()):
        su = f2u.get(su, su)
        su = su.decode('utf-8', 'ignore').encode('utf-8', 'ignore')
        mapping['index_to_source_url'][s_idx] = su
        mapping['source_url_to_index'][su] = s_idx

    for t_idx, tu in enumerate(target_corpus.iterkeys()):
        tu = f2u.get(tu, tu)
        tu = tu.decode('utf-8', 'ignore').encode('utf-8', 'ignore')
        mapping['index_to_target_url'][t_idx] = tu
        mapping['target_url_to_index'][tu] = t_idx

    # print repr(mapping)
    json.dump(mapping, fh)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    # parser.add_argument(
    #     'lettfile', help='input lett file', type=argparse.FileType('r'))
    parser.add_argument(
        'corpus', help='pickled source and target corpus', type=argparse.FileType('r'))
    parser.add_argument(
        '-outfile', help='output file', type=argparse.FileType('w'),
        default=sys.stdout)
    parser.add_argument('feature',
                        choices=['LinkDistance', 'LinkJaccard', 'Simhash',
                                 'TextDistance', 'NGramJaccard',
                                 'Structure', 'GaleChurch', 'TranslatedBOW',
                                 'NGramCounts', 'LinkCounts'])
    parser.add_argument('-dictfile', help='dictionary file for TranslatedBOW')
    parser.add_argument('-targets', help='output file for target matrix',
                        type=argparse.FileType('w'))
    parser.add_argument('-ngram_size', help="length of ngram from Simhash",
                        default=2, type=int)
    parser.add_argument('-xpath', help="xpath for LinkDistance",
                        default="//a/@href")
    parser.add_argument('-urlmapping',
                        help="outfile for url <-> index mapping",
                        type=argparse.FileType('w'))
    parser.add_argument('-term_counts',
                        help="outfile for document frequency",
                        type=argparse.FileType('w'))
    parser.add_argument('-file2url', help='mapping to real url',
                        type=argparse.FileType('r'))
    parser.add_argument('-slang', help='source language', default='en')
    parser.add_argument('-tlang', help='target language', default='fr')
    # parser.add_argument(
    #     '-source_tokenizer', help='call to tokenizer, including arguments')
    # parser.add_argument(
    #     '-target_tokenizer', help='call to tokenizer, including arguments')
    parser.add_argument(
        '-corenlp_service', help='corenlp json service location',
        default='http://localhost:8080')
    parser.add_argument('-threads', type=int,
                        help='number of threads for scoring', default=1)

    args = parser.parse_args(sys.argv[1:])

    pool = None
    if args.threads > 1:
        pool = multiprocessing.Pool(processes=args.threads)

    # source_tokenizer = ExternalProcessor(args.source_tokenizer) \
    #     if args.source_tokenizer else WordPunctTokenizer()
    # target_tokenizer = ExternalProcessor(args.target_tokenizer) \
    #     if args.target_tokenizer else WordPunctTokenizer()

    # read source and target corpus
    sys.stderr.write("Loading %s\n" % (args.corpus.name))
    s = pickle.load(args.corpus)
    t = pickle.load(args.corpus)

    sys.stderr.write("Read %d %s docs and %d %s docs from %s\n" %
                     (len(s), args.slang,
                      len(t), args.tlang, args.corpus.name))

    # if args.targets:
    #     np.savetxt(args.targets, get_ground_truth(s, t))
    if args.urlmapping:
        write_url2dim(s, t, args.urlmapping, args.file2url)
        # sys.exit()  # TODO: remove?

    scorer = None

    print "Using feature: ", args.feature

    if args.feature == 'LinkDistance':
        link_extractor = LinkExtractor(args.xpath)
        scorer = DistanceScorer(extraction_mapper=link_extractor,
                                ratio_function=ratio)
    if args.feature == 'LinkJaccard':
        link_extractor = LinkExtractor(args.xpath)
        scorer = DistanceScorer(extraction_mapper=link_extractor,
                                ratio_function=jaccard,
                                set_based=True)
    elif args.feature == 'TextDistance':
        assert args.ngram_size == 1, "use NGramJaccard instead\n"
        word_extractor = WordExtractor()
        scorer = DistanceScorer(extraction_mapper=word_extractor,
                                ratio_function=quick_ratio)
    elif args.feature == 'NGramJaccard':
        word_extractor = WordExtractor(n=args.ngram_size)
        scorer = DistanceScorer(extraction_mapper=word_extractor,
                                ratio_function=jaccard,
                                set_based=True)
    elif args.feature == 'Structure':
        structure_extractor = StructureExtractor(
            length_function=lambda x: len(x.split()),
            growth_function=lambda x: 1 + math.log(x))
        scorer = DistanceScorer(extraction_mapper=structure_extractor,
                                ratio_function=ratio)
    elif args.feature == 'GaleChurch':
        scorer = GaleChurchScorer()

    elif args.feature == 'Simhash':
        scorer = SimhashDistance(n=args.ngram_size)
    elif args.feature == 'GaleChurch':
        scorer = GaleChurchAlignmentDistance()
    elif args.feature == 'TranslatedBOW':
        assert args.dictfile is not None, "Need dictfile for TranslatedBOW"
        scorer = DictionaryScorer(args.dictfile,
                                  args.slang, args.tlang)
    elif args.feature == 'NGramCounts':
        assert args.term_counts is not None
        word_extractor = EnglishWordExtractor(
            n=args.ngram_size, hash_values=False)
        scorer = DistanceScorer(extraction_mapper=word_extractor,
                                ratio_function=None,
                                set_based=True)
        args.term_counts.write("%d\n" % (len(s) + len(t)))
        for ngram, count in scorer.joined_counts(s, t).iteritems():
            args.term_counts.write("%s\t%d\n" % (ngram.encode('utf-8'), count))
        sys.exit()
    elif args.feature == 'Cosine':
        scorer = CosineDistanceScorer(ngram_size=args.ngram_size,
                                      min_count=1,
                                      counts_file=args.read_term_counts,
                                      metric='cosine')

    elif args.feature == 'LinkCounts':
        pass
    assert scorer is not None, "Need to instantiate scorer first"

    m = scorer.score(s, t, pool=pool)

    # sys.exit()

    # get_best_match(s, t, m)
    # get_best_matching(s, t, m)

    # print "Finding best matching"
    # targets = get_ground_truth(s, t)
    # correct, errors = [], []
    # score_matrix = predicted.reshape((n_source, n_target))
    # score_matrix = m
    # np.savetxt("scores", score_matrix)
    # for s_idx in range(len(s)):
    # print np.argmax(score_matrix[s_idx]), s_idx
    #     t_idx = np.argmax(score_matrix[s_idx])
    # if targets[s_idx * n_target + t_idx] > 0:
    #     if targets[s_idx, t_idx] > 0:
    #         correct.append(s_idx)
    #     else:
    #         errors.append(s_idx)
    # total = len(correct) + len(errors)
    # print "Right: %d/%d, Wrong: %d/%d = %f%%" \
    #     % (len(correct), total, len(errors), total, 100. * len(errors) / total)
    # sys.exit()

    # fix nans.
    if np.sum(np.isnan(m)) > 0:
        sys.stderr.write(
            "found %d nans in matrix of shape %s\n"
            % (np.sum(np.isnan(m)), m.shape))
        m[np.isnan(m)] = 0

    # if np.std(m) > 0:
    #     m = (m - np.mean(m)) / np.std(m)

    np.savetxt(args.outfile, m)
    sys.exit()

    # print info
    try:
        ranks = list(get_ranks(s, t, m))
        sys.stderr.write("Avg. Rank: %f\n" % (float(sum(ranks)) / len(ranks)))
        n_errors = sum(1 for r in ranks if r > 0)
        print "Err: %d / %d = %f%%" % (n_errors, len(ranks),
                                       100. * float(n_errors) / len(ranks))
    except:
        ValueError
    # print sum(1 for r in ranks if r < 20)
    get_nbest(s, t, m, n=20)

    sys.exit()

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

#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime
from scipy.stats import pearsonr, spearmanr
from sklearn.linear_model import LogisticRegression, LogisticRegressionCV
import gzip
import json
import numpy as np
import pickle
import sys
from sklearn import preprocessing
from collections import defaultdict

# sys.path.append("/home/buck/net/build/DataCollection/baseline")
# from strip_language_from_uri import LanguageStripper


def read_devset(fh, mapping):
    # format fr-url <TAB> en-url
    devset = set()
    print "Reading devset from ", fh.name
    for line in fh:
        surl, turl = line.strip().split()
        if surl in mapping['source_url_to_index']:
            assert turl in mapping['target_url_to_index']
        if turl in mapping['target_url_to_index']:
            assert surl in mapping['source_url_to_index']
            tidx = mapping['target_url_to_index'][turl]
            sidx = mapping['source_url_to_index'][surl]
            devset.add((sidx, tidx))

    return devset


def read_devset_multi(fh, mapping, deduped):
    # format fr-url <TAB> en-url
    devset = set()
    n_pairs = 0
    print "Reading multi-devset from ", fh.name
    for line in fh:
        surls, turls = line.split('\t<->\t')
        surls = surls.strip().split('\t')
        turls = turls.strip().split('\t')

        added = False
        for surl in surls:
            if surl in mapping['source_url_to_index']:
                found_turl = sum(
                    1 for turl in turls if
                    turl in mapping['target_url_to_index'])
                if deduped:
                    assert found_turl == 1
                else:
                    assert found_turl == len(turls)

                for turl in turls:
                    if turl in mapping['target_url_to_index']:
                        assert surl in mapping['source_url_to_index']
                        tidx = mapping['target_url_to_index'][turl]
                        sidx = mapping['source_url_to_index'][surl]
                        devset.add((sidx, tidx))
                        added = True
        if added:
            n_pairs += 1

    return devset, n_pairs


def load_seeds(fh, mapping):
    seeds = []
    seen = set()
    known_urls = set(mapping['target_url_to_index'].keys())
    known_urls.update(mapping['source_url_to_index'].keys())
    for line in fh:
        su, tu = line.strip().split('\t')
        if tu not in known_urls:
            continue
        if su not in known_urls:
            continue

        if tu not in mapping['target_url_to_index'] \
                or su not in mapping['source_url_to_index']:
            # print 'swapping', su, tu
            su, tu = tu, su

        # if su not in mapping['source_url_to_index']:
        # wrong domain
        #     assert tu not in mapping['target_url_to_index']
        #     assert tu not in mapping['source_url_to_index']
        #     assert su not in mapping['target_url_to_index']
        #     continue
        # assert tu in mapping['target_url_to_index']
        # assert su in mapping['source_url_to_index']
        if su in seen:
            continue
        if tu in seen:
            continue
        sidx = mapping['source_url_to_index'][su]
        tidx = mapping['target_url_to_index'][tu]
        seeds.append((sidx, tidx))
    return seeds


def find_pairs_in_devset(matches, devset):
    # If we get one from a group we score a win
    # but also invalidate all other entries from that
    # group
    s2t = defaultdict(set)
    t2s = defaultdict(set)
    for si, ti in devset:
        s2t[si].add(ti)
        t2s[ti].add(si)

    seen_s, seen_t = set(), set()
    found = []
    fails = []

    for rank, (si, ti) in enumerate(matches):
        if si in seen_s or ti in seen_t:
            fails.append()
            continue
        if si in s2t and ti in s2t[si]:
            found.append((si, ti, rank))
            seen_s.update(t2s[ti])
            seen_t.update(s2t[si])
    return found


# def find_missing(devset, found_matches):
#     sis = set([si for si, ti in found_matches])
#     tis = set([ti for si, ti in found_matches])
#     for si, ti in devset:
#         if (si, ti) in devset:
#             continue
#         if

def translate_matches(matches, mapping):
    res = []
    for m in matches:
        si, ti = m[:2]
        surl = mapping['index_to_source_url'][str(si)]
        turl = mapping['index_to_target_url'][str(ti)]
        res.append([surl, turl])
        res[-1].extend(m[2:])
    return res


def read_idx2url(fh):
    mapping = json.load(fh)
    return mapping

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-devset', help='WMT16 devset',
                        type=argparse.FileType('r'), required=True)
    parser.add_argument('-idx2url', help='url to index mapping',
                        type=argparse.FileType('r'), required=True)
    parser.add_argument('-read_model',
                        help='read fitted model',
                        type=argparse.FileType('rb'))
    parser.add_argument('feature_matrix', nargs='*',
                        help='precomputed matrix for single feature',
                        type=argparse.FileType('r'))
    parser.add_argument('-matching',
                        help='compute max-cost matching',
                        action='store_true')
    parser.add_argument('-prefix',
                        help='output prefix (domain name)',
                        default="PREFIX")
    parser.add_argument('-scale',
                        help='scale input matrices',
                        action='store_true')
    parser.add_argument('-multi',
                        help='n:m devset',
                        action='store_true')
    parser.add_argument('-deduped',
                        help='lett files were deduped',
                        action='store_true')
    parser.add_argument('-write_matrix',
                        help='write concatenated feature matrix',
                        type=argparse.FileType('w'))
    parser.add_argument('-write_predictions',
                        help='write predicted values',
                        type=argparse.FileType('w'))
    parser.add_argument('-load_predictions',
                        help='load prediction matrix',
                        type=argparse.FileType('r'))
    parser.add_argument('-write_matches',
                        help='write matches to this file',
                        type=argparse.FileType('w'))
    parser.add_argument('-write_found',
                        help='write found matches to this file',
                        type=argparse.FileType('w'))
    parser.add_argument('-write_fails',
                        help='write missing pairs to this file',
                        type=argparse.FileType('w'))
    parser.add_argument('-seed',
                        help='initial pairs',
                        type=argparse.FileType('r'))

    args = parser.parse_args(sys.argv[1:])
    print "CMD: ", " ".join(sys.argv)

    url_mapping = read_idx2url(args.idx2url)
    devset = None
    devset_size = 0
    if args.multi:
        devset, devset_size = read_devset_multi(args.devset,
                                                url_mapping,
                                                args.deduped)
    else:
        devset = read_devset(args.devset, url_mapping)
        devset_size = len(devset)
    print "Loaded %d/%d expected pairs from %s" % (
        devset_size, len(devset), args.devset.name)

    score_matrix = None
    if args.feature_matrix:
        print "Loading model from ", args.read_model.name
        fitted_model = pickle.load(args.read_model)
        # print "Coef:", fitted_model.coef_

        n_features = len(args.feature_matrix)
        n_samples, n_source, n_target = None, None, None
        m = None

        for f_idx, f_file in enumerate(args.feature_matrix):
            print "Loading features from ", f_file.name
            fh = f_file
            if f_file.name.endswith('.gz'):
                fh = gzip.GzipFile(fileobj=fh, mode='r')
            f = np.load(fh)
            if args.scale:
                print "scaling"
                f = preprocessing.scale(f)
            # f = f.astype(np.float32, copy=False)

            if m is None:
                n_samples = f.size
                n_source, n_target = f.shape
                m = np.zeros((n_samples, n_features), dtype=np.float64)
            else:
                assert f.shape == (n_source, n_target)
            m[:, f_idx] = f.flatten()

        print datetime.now()

        print "%d source / %d target docs / %d features" \
            % (n_source, n_target, n_features)

        if args.write_matrix:
            np.save(args.write_matrix, m)

        print "Predicting %d instances." % (m.shape[0])
        predicted = None
        if hasattr(fitted_model, "predict_proba"):
            predicted = fitted_model.predict_proba(m)[:, 1]
        else:  # use decision function
            print "Using predict instead of predict_proba"
            prob_pos = fitted_model.predict(m)
            predicted = (prob_pos - prob_pos.min()) / \
                (prob_pos.max() - prob_pos.min())

        # predicted = fitted_model.predict_proba(m)
        # predicted = predicted[:, 1]  # we're interested in probs for class 1
        del m

        print predicted
        score_matrix = predicted.reshape((n_source, n_target))

        if args.write_predictions:
            np.save(args.write_predictions, score_matrix)
            # evaluate later
            sys.exit()

    else:
        assert args.load_predictions
        fh = args.load_predictions
        if fh.name.endswith('.gz'):
            fh = gzip.GzipFile(fileobj=fh, mode='r')
        score_matrix = np.load(fh)
        print "Loaded matrix of shape", score_matrix.shape, \
              " from ", args.load_predictions.name

    print datetime.now()
    matches = []
    if args.matching:
        print "Finding best matching"

        full_matrix = np.pad(
            score_matrix,
            ((0, max(score_matrix.shape) - score_matrix.shape[0]),
             (0, max(score_matrix.shape) - score_matrix.shape[1])),
            mode='constant')

        # print full_matrix.shape, np.sum(full_matrix)
        # print score_matrix.shape, np.sum(score_matrix)

        import dlib
        cost = dlib.matrix(full_matrix)
        print "Searching with dlib"
        assignment = dlib.max_cost_assignment(cost)
        # print assignment

        for sidx, tidx in enumerate(assignment):
            if sidx >= score_matrix.shape[0] or tidx >= score_matrix.shape[1]:
                continue
            matches.append((score_matrix[sidx, tidx], sidx, tidx))

        matches.sort(reverse=True)
        matches = [(sidx, tidx) for score, sidx, tidx in matches]

    else:
        print "Finding best match (greedy / restricted + argsort)"
        seen_cols = set()
        seen_rows = set()

        if args.seed:
            seeds = load_seeds(args.seed, url_mapping)
            print "Loaded %d seeds from %s" % (len(seeds), args.seed.name)
            for sidx, tidx in seeds:
                matches.append((sidx, tidx))
                seen_cols.add(tidx)
                seen_rows.add(sidx)

        n_cols = score_matrix.shape[1]
        max_matches = min(score_matrix.shape)
        sorted_indices = np.argsort(score_matrix, axis=None, kind='mergesort')
        for idx in sorted_indices[::-1]:
            am_row = idx / n_cols
            if am_row in seen_rows:
                continue
            am_col = idx - am_row * n_cols
            # am_row, am_col = np.unravel_index(idx, score_matrix.shape)
            if am_col in seen_cols:
                continue
            matches.append((am_row, am_col))
            seen_cols.add(am_col)
            seen_rows.add(am_row)
            if len(matches) >= max_matches:
                break

    match_costs = [score_matrix[r, c] for r, c in matches]
    # matches = set(matches)
    print "Found %d matches, total cost %.5f" % (
        len(matches), sum(match_costs) / len(matches))
    found = find_pairs_in_devset(matches, devset)
    if devset_size == 0:
        devset_size = 1
    print "Found %d out of %d pairs = %f%%" \
        % (len(found), len(devset), 100. * len(found) / devset_size)
    found_costs = [score_matrix[r, c] for r, c, rank in found]
    found_ranks = [rank for r, c, rank in found]
    name = None
    if args.read_model:
        name = args.read_model.name
    else:
        assert args.load_predictions
        name = args.load_predictions.name
    print "RES:\t%s\t%s\t%d\t%d" % (args.prefix, name,
                                    len(found), devset_size)
#    print "SCORES:\t%s\t%f\t%f\t%f\t%f" % (args.prefix,
#                                           sum(found_costs),
#                                           min(found_costs),
#                                           sum(match_costs),
#                                           sum(match_costs) / len(matches))
#    print "RANKS:\t%s\t%d\t%d" % (args.prefix,
#                                  max(found_ranks),
#                                  min(found_ranks))
    print datetime.now()

    if args.write_found:
        matching_urls = translate_matches(found, url_mapping)
        for (surl, turl, rank), cost in zip(matching_urls, found_costs):
            args.write_found.write(
                "%.30f %d %s %s\n" % (cost, rank, surl, turl))

    if args.write_matches:
        buf = []
        matching_urls = translate_matches(matches, url_mapping)
        for (surl, turl), cost in zip(matching_urls, match_costs):
            buf.append((cost, surl, turl))
        buf.sort(reverse=True)
        rank = 0
        for cost, surl, turl in buf:
            args.write_matches.write(
                "%.30f %d %s %s\n" % (cost, rank,
                                      surl.encode('utf-8'),
                                      turl.encode('utf-8')))
            rank += 1

    # if args.write_fails:
    #     missing =
    #     for sidx, tidx in devset:

    sys.exit()

#!/usr/bin/env python
# -*- coding: utf-8 -*-
import numpy as np
import sys
import json
import pickle
from datetime import datetime
from scipy.stats import pearsonr, spearmanr
from sklearn.linear_model import LogisticRegression, LogisticRegressionCV
from sklearn import linear_model

sys.path.append("/home/buck/net/build/DataCollection/baseline")
from strip_language_from_uri import LanguageStripper


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


# def read_devset(fh, mapping):
# format fr-url <TAB> en-url
#     devset = set()
#     url_matched = []
#     stripper = LanguageStripper()
#     print "Reading devset from ", fh.name
#     seen = set()
#     for line in fh:
#         turl, surl = line.strip().split()
#         if turl not in seen and surl not in seen:
#             if turl not in mapping['target_url_to_index']:
#                 if "creationwiki.org" in turl:
#                     sys.stderr.write("Unknown target URL: %s\n" % turl)
#             elif surl not in mapping['source_url_to_index']:
#                 if "creationwiki.org" in surl:
#                     sys.stderr.write("Unknown source URL: %s\n" % surl)
#             else:
#                 assert turl in mapping['target_url_to_index']
#                 assert surl in mapping['source_url_to_index']
#                 tidx = mapping['target_url_to_index'][turl]
#                 sidx = mapping['source_url_to_index'][surl]
#                 devset.add((sidx, tidx))
#                 seen.add(turl)
#                 seen.add(surl)

# print stripper.strip(surl), stripper.strip(turl)
#                 if stripper.strip(surl) == stripper.strip(turl):
#                     url_matched.append((surl, turl))

#         else:
#             print "already seen:"
#             print surl, turl
#             print devset
#             sys.exit()

#     print "url_matched:", len(url_matched), "/", len(devset)
# sys.exit()
#     return devset


def read_idx2url(fh):
    mapping = json.load(fh)
    return mapping


# def cut_features(feature_list, devset, mapping):
# col = targets
# rows = sources
#     cols, rows = [], []
#     for turl, surl in devset.iteritems():
#         cols.append(mapping['target_url_to_index'][turl])
#         rows.append(mapping['source_url_to_index'][surl])
#     cols.sort()
#     rows.sort()

# We have 1-1 mapping which gives a square matrix
#     new_target = np.zeros((len(rows), len(cols)))

#     for turl, surl in devset.iteritems():
#         sidx = mapping['source_url_to_index'][surl]
#         sidx = rows.index(sidx)
#         tidx = mapping['target_url_to_index'][turl]
#         tidx = cols.index(tidx)

#         new_target[sidx, tidx] = 1

#     new_features = []
#     for f in features:
#         print f.shape
#         print (len(mapping['source_url_to_index']),
#                len(mapping['target_url_to_index']))
#         assert f.shape == (len(mapping['source_url_to_index']),
#                            len(mapping['target_url_to_index']))
#         nf = f[rows][:, cols]
#         new_features.append(nf)

#     return new_features, new_target

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
    parser.add_argument('feature_matrix', nargs='+',
                        help='precomputed matrix for single feature',
                        type=argparse.FileType('r'))
    parser.add_argument('-matching',
                        help='compute max-cost matching',
                        action='store_true')
    parser.add_argument('-prefix',
                        help='output prefix (domain name)',
                        default="PREFIX")

    args = parser.parse_args(sys.argv[1:])

    print "Loading model from ", args.read_model.name
    fitted_model = pickle.load(args.read_model)
    # print "Coef:", fitted_model.coef_

    url_mapping = read_idx2url(args.idx2url)
    devset = read_devset(args.devset, url_mapping)
    print "Loaded %d expected pairs from %s" % (len(devset), args.devset.name)

    # print "Loading features from ", [fh.name for fh in args.feature_matrix]
    # features = map(np.load, args.feature_matrix)

    # n_source, n_target = features[0].shape

    n_features = len(args.feature_matrix)
    n_samples, n_source, n_target = None, None, None
    m = None

    for f_idx, f_file in enumerate(args.feature_matrix):
        print "Loading features from ", f_file.name
        f = np.load(f_file)
        if m is None:
            n_samples = f.size
            n_source, n_target = f.shape
            m = np.zeros((n_samples, n_features))
        else:
            assert f.shape == (n_source, n_target)
        m[:, f_idx] = f.flatten()

    print "%d source / %d target docs / %d features" \
        % (n_source, n_target, n_features)

    # TODO: make this more elegant
    # for s_idx in range(n_source):
    #     for t_idx in range(n_target):

    #         sample_idx = s_idx * n_target + t_idx

    #         for f_idx in range(n_features):
    #             m[sample_idx, f_idx] = features[f_idx][s_idx, t_idx]

    print "Predicting %d instances." % (m.shape[0])
    predicted = fitted_model.predict_proba(m)
    predicted = predicted[:, 1]  # we're interested in probs for class 1

    score_matrix = predicted.reshape((n_source, n_target))

    # print datetime.now()
    # print "Finding best match (greedy)"
    # greedy_matches = set()
    # correct, errors = [], []
    # for s_idx in range(n_source):
    #     t_idx = np.argmax(score_matrix[s_idx])
    #     greedy_matches.add((s_idx, t_idx))

    # found = devset.intersection(greedy_matches)
    # print "Found %d matches " % (len(greedy_matches))
    # print "Found %d out of %d pairs = %f%%" \
    #     % (len(found), len(devset), 100. * len(found) / len(devset))

    # print datetime.now()
    # print "Finding best match (greedy / restricted)"
    # matches = set()
    # correct, errors = [], []
    # score_copy = score_matrix.copy()
    # while True:
    #     am = np.argmax(score_copy)
    #     am_row, am_col = np.unravel_index(am, score_copy.shape)
    #     if score_copy[am_row, am_col] <= 0:
    #         break
    #     matches.add((am_row, am_col))
    #     score_copy[am_row, :] = -np.inf
    #     score_copy[:, am_col] = -np.inf
    # del score_copy
    # print "Found %d matches " % (len(matches))
    # found = devset.intersection(matches)
    # print "Found %d out of %d pairs = %f%%" \
    #     % (len(found), len(devset), 100. * len(found) / len(devset))

    print datetime.now()
    print "Finding best match (greedy / restricted + argsort)"
    matches = set()
    seen_cols = set()
    seen_rows = set()
    sorted_indices = np.argsort(score_matrix, axis=None)
    for idx in sorted_indices[::-1]:
        am_row, am_col = np.unravel_index(idx, score_matrix.shape)
        if am_row in seen_rows or am_col in seen_cols:
            continue
        matches.add((am_row, am_col))
        seen_cols.add(am_col)
        seen_rows.add(am_row)

    print "Found %d matches " % (len(matches))
    # print greedy_matches
    found = devset.intersection(matches)
    print "Found %d out of %d pairs = %f%%" \
        % (len(found), len(devset), 100. * len(found) / len(devset))

    print "RES:\t%s\t%s\t%d\t%d" % (args.prefix, args.read_model.name,
                                    len(found), len(devset))

    #

    print datetime.now()
    if args.matching:
        print "Finding best matching"
        matching_pairs = set()

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
            matching_pairs.add((sidx, tidx))

        print "Found %d matches " % (len(matching_pairs))
        # print greedy_matches
        found = devset.intersection(matching_pairs)
        print "Found %d out of %d pairs = %f%%" \
            % (len(found), len(devset), 100. * len(found) / len(devset))
        print datetime.now()

    sys.exit()

    matching_pairs = set()
    m = munkres.Munkres()
    cost_matrix = munkres.make_cost_matrix(
        score_matrix, lambda cost: 1000 - cost)
    indexes = m.compute(cost_matrix)
    for row, column in indexes:
        matching_pairs.add((row, column))

    found = devset.intersection(matching_pairs)
    print "Found %d out of %d pairs = %f%%" \
        % (len(found), len(devset), 100. * len(found) / len(devset))

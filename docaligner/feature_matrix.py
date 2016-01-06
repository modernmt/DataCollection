#!/usr/bin/env python
# -*- coding: utf-8 -*-
import math
import numpy as np
import sys
import json
import pickle

from scipy.stats import pearsonr, spearmanr
from sklearn import svm
from sklearn import cross_validation
from sklearn import tree
from unbalanced_dataset import UnderSampler, OverSampler
from sklearn.cross_validation import StratifiedKFold
from sklearn.ensemble import ExtraTreesClassifier
from sklearn import metrics
from sklearn.linear_model import LogisticRegression, LogisticRegressionCV
from sklearn import linear_model
from sklearn.grid_search import GridSearchCV
from sklearn import neighbors
from sklearn import naive_bayes


def read_devset(fh, mapping):
    # format fr-url <TAB> en-url
    devset = {}
    print "Reading devset from ", fh.name
    for line in fh:
        turl, surl = line.strip().split()
        if turl in mapping['target_url_to_index'] and \
                surl in mapping['source_url_to_index']:
            assert surl not in devset.values()
            assert turl not in devset
            devset[turl] = surl

    return devset


def read_idx2url(fh):
    mapping = json.load(fh)
    return mapping


def cut_features(feature_list, devset, mapping):
    # col = targets
    # rows = sources
    cols, rows = [], []
    for turl, surl in devset.iteritems():
        cols.append(mapping['target_url_to_index'][turl])
        rows.append(mapping['source_url_to_index'][surl])
    cols.sort()
    rows.sort()

    # We have 1-1 mapping which gives a square matrix
    new_target = np.zeros((len(rows), len(cols)))

    for turl, surl in devset.iteritems():
        sidx = mapping['source_url_to_index'][surl]
        sidx = rows.index(sidx)
        tidx = mapping['target_url_to_index'][turl]
        tidx = cols.index(tidx)

        new_target[sidx, tidx] = 1

    new_features = []
    for f in features:
        print f.shape
        print (len(mapping['source_url_to_index']),
               len(mapping['target_url_to_index']))
        assert f.shape == (len(mapping['source_url_to_index']),
                           len(mapping['target_url_to_index']))
        nf = f[rows][:, cols]
        new_features.append(nf)

    return new_features, new_target

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-targets',
                        help='target matrix',
                        type=argparse.FileType('r'),
                        required=True)
    parser.add_argument('-devset', help='WMT16 devset',
                        type=argparse.FileType('r'))
    parser.add_argument('-idx2url', help='url to index mapping',
                        type=argparse.FileType('r'))
    parser.add_argument('-write_train',
                        help='write training instances',
                        type=argparse.FileType('wb'),
                        required=True)
    parser.add_argument('feature_matrix', nargs='+',
                        help='precomputed matrix for single feature',
                        type=argparse.FileType('r'))

    args = parser.parse_args()

    targets, m = None, None
    n_source, n_target, n_samples = None, None, None

    print "Loading targets from ", args.targets.name
    targets = np.loadtxt(args.targets)
    print "Loading features from ", [fh.name for fh in args.feature_matrix]
    features = map(np.loadtxt, args.feature_matrix)
    n_features = len(features)

    url_mapping = None
    if args.idx2url:
        url_mapping = read_idx2url(args.idx2url)

    devset = None
    if args.devset:
        assert url_mapping is not None, 'also need idx-url mapping'
        devset = read_devset(args.devset, url_mapping)
        features, targets = cut_features(features, devset, url_mapping)

    n_source, n_target = features[0].shape

    print "%d source / %d target docs / %d features" \
        % (n_source, n_target, n_features)

    n_samples = n_source * n_target
    m = np.zeros((n_samples, n_features))

    for s_idx in range(n_source):
        for t_idx in range(n_target):
            c = 0.0  # the class to predict
            if s_idx == t_idx:
                c = 1.

            sample_idx = s_idx * n_target + t_idx

            for f_idx in range(n_features):
                m[sample_idx, f_idx] = features[f_idx][s_idx, t_idx]

    print "Writing to ", args.write_train.name
    np.savez(args.write_train,
             targets=targets.reshape((n_source, n_target)),
             feature_matrix=m)

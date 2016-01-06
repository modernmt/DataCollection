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


# for Hungarian Algorithm
import munkres

# mapping = {'index_to_source_url': {},
#            'index_to_target_url': {},
#            'source_url_to_index': {},
#            'target_url_to_index': {}}


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
    parser.add_argument('targets',
                        help='target matrix',
                        type=argparse.FileType('r'))
    parser.add_argument('-devset', help='WMT16 devset',
                        type=argparse.FileType('r'))
    parser.add_argument('-idx2url', help='url to index mapping',
                        type=argparse.FileType('r'))

    parser.add_argument('feature_matrix', nargs='+',
                        help='precomputed matrix for single feature',
                        type=argparse.FileType('r'))
    parser.add_argument('-write_train',
                        help='write training instances',
                        type=argparse.FileType('wb'))
    parser.add_argument('-read_train', nargs='+',
                        help='read training instances',
                        type=argparse.FileType('rb'))
    parser.add_argument('-write_model',
                        help='write fitted model',
                        type=argparse.FileType('wb'))
    parser.add_argument('-read_model',
                        help='read fitted model',
                        type=argparse.FileType('rb'))
    # parser.add_argument(
    #     '-outfile', help='output file', type=argparse.FileType('w'),
    #     default=sys.stdout)
    # parser.add_argument('feature',
    #                     choices=['LinkDistance', 'BOW', 'Simhash',
    #                              'Structure'])
    # parser.add_argument('-ngram_size', help="length of ngram from Simhash",
    #                     default=2, type=int)
    # parser.add_argument('-xpath', help="xpath for LinkDistance",
    #                     default="//a/@href")
    # parser.add_argument('-slang', help='source language', default='en')
    # parser.add_argument('-tlang', help='target language', default='fr')
    # parser.add_argument(
    #     '-corenlp_service', help='corenlp json service location',
    #     default='http://localhost:8080')

    args = parser.parse_args(sys.argv[1:])

    targets, m = None, None
    n_source, n_target, n_samples = None, None, None

    if not args.read_train:
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

        # np.savetxt("m", m)

    else:
        for f in args.read_train:
            npzfile = np.load(f)
            if targets is None:
                targets = npzfile['targets']
                n_source, n_target = targets.shape

                m = npzfile['feature_matrix']
            else:
                np.concatenate(targets, npzfile['targets'], axis=0)
                assert npzfile['targets'] == targets
                np.concatenate(m, npzfile['feature_matrix'])
        n_source, n_target = targets.shape
        n_samples = m.shape[0]
        assert m.shape[0] == targets.shape[0]

    if args.write_train:
        np.savez(args.write_train,
                 targets=targets.reshape((n_source, n_target)),
                 feature_matrix=m)

    targets = targets.reshape(n_samples)
    print "Sum of targets: ", sum(targets)

    print "instances x features: ", m.shape

    ratio = float(np.count_nonzero(targets == 0)) / \
        float(np.count_nonzero(targets == 1))
    print "Ratio 0 vs. 1: ", ratio

    # US = OverSampler(ratio=ratio, verbose=True)
    # US = UnderSampler(verbose=True)
    # m, targets = US.fit_transform(m, targets)

    fitted_model = None

    if args.read_model:
        fitted_model = pickle.load(args.read_model)
    else:
        skf = cross_validation.StratifiedKFold(targets, 5)
        print "Running stratified 5-fold CV"

        params_space = {}
        # clf = svm.SVC(gamma=0.001, C=100., class_weight='balanced')
        # clf = svm.SVC(gamma=0.001, C=100., probability=True)
        clf = tree.DecisionTreeClassifier()
        clf = clf.fit(m, targets)
        print clf.feature_importances_

        # params_space = {'kernel': ['linear', 'poly', 'rbf'],
        #                 "C": [1e-1, 1e0, 1e1, 1e2, 1e3, 1e4]}

        # clf = ExtraTreesClassifier(n_estimators=500,
        #                            random_state=0)
        # clf = LogisticRegression(class_weight='balanced')
        # params_space = {'kernel': ['linear', 'poly', 'rbf'],
        #                 "C": [1e-1, 1e0, 1e1, 1e2, 1e3, 1e4]}
        clf = svm.SVR()

        # clf = svm.SVC(class_weight='balanced', probability=True)
        # params_space = {'C': np.logspace(-1, 4, 6), 'gamma': np.logspace(-2, 2, 5)}

        # clf = GridSearchCV(svm.SVR(kernel='rbf', gamma=0.1), cv=5,
        #                    param_grid={"C": [1e-1, 1e0, 1e1, 1e2, 1e3, 1e4],
        #                                "gamma": np.logspace(-2, 2, 5)})
        # clf = linear_model.LinearRegression()

        # clf = linear_model.RidgeCV(alphas=[0.01, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0])
        # clf = linear_model.BayesianRidge()
        # clf = linear_model.Ridge()
        # clf = linear_model.ElasticNet()
        # clf = neighbors.KNeighborsRegressor(n_neighbors=10, weights='distance')
        # clf = naive_bayes.GaussianNB()

        # scoring = 'f1'

        gs = GridSearchCV(clf, params_space, n_jobs=-1, cv=skf)
        gs.fit(m, targets.reshape(n_samples))
        print "Best parameters found in CV:", gs.best_params_
        fitted_model = gs

    if args.write_model:
        print "Loading model"
        pickle.dump(fitted_model, args.write_model)

    predicted = fitted_model.predict_proba(m)
    predicted = predicted[:, 1]  # we're interested in probs for class 1

    # predicted = cross_validation.cross_val_predict(
    #     clf, m, targets.reshape(n_samples), cv=skf)
    print targets[:5], predicted[:5]

    print "Finding best match"
    targets = targets.reshape((n_source, n_target))
    correct, errors = [], []
    score_matrix = predicted.reshape((n_source, n_target))
    # score_matrix = features[-1]
    np.savetxt("scores", score_matrix)
    for s_idx in range(n_source):
        t_idx = np.argmax(score_matrix[s_idx])
        if targets[s_idx, t_idx] > 0:
            correct.append(s_idx)
        else:
            errors.append(s_idx)
    total = len(correct) + len(errors)
    print "Right: %d/%d = %f%%, Wrong: %d/%d = %f%%" \
        % (len(correct), total, 100. * len(correct) / total,
           len(errors), total, 100. * len(errors) / total)

    print "Finding best matching"
    m = munkres.Munkres()
    correct, errors = [], []
    cost_matrix = munkres.make_cost_matrix(score_matrix, lambda cost: 1 - cost)
    indexes = m.compute(cost_matrix)
    for row, column in indexes:
        if targets[row, column] > 0:
            correct.append((row, column))
        else:
            errors.append((row, column))
    total = len(correct) + len(errors)
    print "Right: %d/%d = %f%%, Wrong: %d/%d = %f%%" \
        % (len(correct), total, 100. * len(correct) / total,
           len(errors), total, 100. * len(errors) / total)

    # scores = cross_validation.cross_val_score(
    #     clf, m, targets, cv=5, scoring=scoring)
    # print sum(predicted), sum(predicted - targets)
    # print metrics.classification_report(targets, predicted)
    # print metrics.f1_score(targets, predicted)
    # print metrics.accuracy_score(targets, predicted)

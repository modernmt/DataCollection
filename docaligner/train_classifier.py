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
from unbalanced_dataset import UnderSampler, OverSampler, SMOTE, SMOTEENN, SMOTETomek
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
        surl, turl = line.strip().split()
        if turl in mapping['target_url_to_index']:
            assert surl in mapping['source_url_to_index']
            assert surl not in devset.values()
            assert turl not in devset
            devset[surl] = turl

    return devset


def read_idx2url(fh):
    mapping = json.load(fh)
    return mapping


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('read_train', nargs='+',
                        help='read training instances',
                        type=argparse.FileType('rb'))
    parser.add_argument('-write_model',
                        help='write fitted model',
                        type=argparse.FileType('wb'))
    parser.add_argument('-smote',
                        help='scale input matrices',
                        action='store_true')

    args = parser.parse_args(sys.argv[1:])

    targets, m = None, None
    n_source, n_target, n_samples = None, None, None

    for f in args.read_train:
        npzfile = np.load(f)
        print "Read %d instances from %s" \
            % (npzfile['feature_matrix'].shape[0], f.name)
        assert npzfile['targets'].size == npzfile['feature_matrix'].shape[0]

        tgt, fm = npzfile['targets'], npzfile['feature_matrix']
        print "target size: ", tgt.shape
        print "positive examples: ", sum(sum(tgt))
        tgt = tgt.reshape(tgt.size)
        if args.smote:
            ratio = float(np.count_nonzero(tgt == 0)) / \
                float(np.count_nonzero(tgt == 1))
            OS = SMOTE(ratio=ratio, kind='regular')
            fm, tgt = OS.fit_transform(fm, tgt)

        if targets is None:
            targets = tgt
            m = fm
        else:
            print "Before concat: ", targets.shape, tgt.shape
            targets = np.concatenate((targets, tgt), axis=0)
            m = np.concatenate((m, fm), axis=0)
            print "After concat: ", targets.shape, tgt.shape

    assert targets.size == m.shape[0]
    assert m.shape[0] == targets.shape[0]

    print "Sum of targets: ", sum(targets)
    print "Instances x features: ", m.shape

    ratio = float(np.count_nonzero(targets == 0)) / \
        float(np.count_nonzero(targets == 1))
    print "Ratio 0 vs. 1: ", ratio

    # 'Random over-sampling'
    #OS = OverSampler(ratio=ratio)
    # OS = SMOTE(ratio=ratio, kind='regular')
    # m, targets = OS.fit_transform(m, targets)
    print "Sum of targets: ", sum(targets)
    print "Instances x features: ", m.shape

    skf = cross_validation.StratifiedKFold(targets, 5)
    # print "Running stratified 5-fold CV"

    params_space = {}
    # clf = svm.SVC(gamma=0.001, C=100., class_weight='balanced')
    clf = svm.SVC(gamma=0.001, C=1000., probability=True)
    # clf = tree.DecisionTreeClassifier()
    # clf = clf.fit(m, targets)
    # print clf.feature_importances_

    # params_space = {'kernel': ['linear', 'poly', 'rbf'],
    #                 "C": [1e-1, 1e0, 1e1, 1e2, 1e3, 1e4],
    #                 'gamma': np.logspace(-2, 2, 5)}

    # params_space = {"C": [1e-1, 1e0, 1e1, 1e2, 1e3, 1e4]}
    # params_space = {'gamma': np.logspace(-3, 2, 6)}

    # clf = ExtraTreesClassifier(n_estimators=500,
    #                           random_state=0,
    #                           class_weight='balanced')
    #params_space = {'C': np.logspace(-1, 7, 9)}
    # print params_space
    #clf = LogisticRegression(class_weight='balanced')
    # params_space = {'kernel': ['linear', 'poly', 'rbf'],
    #                 "C": [1e-1, 1e0, 1e1, 1e2, 1e3, 1e4]}
    # clf = svm.SVR()

    # clf = svm.SVC(class_weight='balanced', probability=True)
    # params_space = {'C': np.logspace(-1, 5, 7), 'gamma': np.logspace(-2, 2, 5)}

    # clf = GridSearchCV(svm.SVR(kernel='rbf', gamma=0.1), cv=5,
    #                    param_grid={"C": [1e-1, 1e0, 1e1, 1e2, 1e3, 1e4],
    #                                "gamma": np.logspace(-2, 2, 5)})
    #clf = linear_model.LinearRegression()

    #clf = linear_model.RidgeCV(alphas=[0.01, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0])
    #from sklearn import gaussian_process
    #clf = gaussian_process.GaussianProcess(theta0=1e-2, thetaL=1e-4, thetaU=1e-1)
    # clf = linear_model.BayesianRidge()
    #clf = linear_model.Ridge()
    #clf = linear_model.ElasticNet()
    #clf = neighbors.KNeighborsRegressor(n_neighbors=10, weights='distance')
    #clf = naive_bayes.GaussianNB()
    #from sklearn.svm import LinearSVC
    # clf=LinearSVC(C=1000.0)

    #clf = svm.SVC(gamma=0.01, C=1000., class_weight='balanced', probability=True)
    # clf = svm.SVC(gamma=0.001, C=10000., probability=True, class_weight='balanced')
    clf = LogisticRegression(class_weight='balanced', C=10000)
    # clf = LogisticRegression(class_weight='balanced')

    if args.write_model:
        fitted_model = clf.fit(m, targets.reshape(n_samples))
        print "Writing model to", args.write_model.name
        pickle.dump(fitted_model, args.write_model)

        scoring = 'f1'
        predicted = fitted_model.predict(m)

        print sum(predicted), sum(predicted - targets)
        # print metrics.classification_report(targets, predicted)
        # print metrics.f1_score(targets, predicted)
        # print metrics.accuracy_score(targets, predicted)
        sys.exit()

    scoring = 'f1'
    scores = cross_validation.cross_val_score(
        clf, m, targets, cv=5, scoring=scoring, n_jobs=-1)
    print scores

    # clf = Classifier(
    #     layers=[
    #         Layer("Sigmoid", units=100, dropout=0.25),
    #         Layer("Softmax", dropout=0.25)],
    #     learning_rate=0.001,
    #     batch_size=32,
    #     n_iter=100)

    scores = cross_validation.cross_val_score(
        clf, m, targets, cv=5, scoring=scoring, n_jobs=-1)
    print " 5-CV Scores: ", scores, np.mean(scores)

    scores = cross_validation.cross_val_score(
        clf, m, targets, cv=10, scoring=scoring, n_jobs=-1)
    print "10-CV Scores: ", scores, np.mean(scores)

    scores = cross_validation.cross_val_score(
        clf, m, targets, cv=20, scoring=scoring, n_jobs=-1)
    print "20-CV Scores: ", scores, np.mean(scores)

    print "Running stratified 5-fold CV"
    skf = cross_validation.StratifiedKFold(targets, 5)
    gs = GridSearchCV(clf, params_space, n_jobs=-1, cv=skf, scoring='f1')
    gs.fit(m, targets.reshape(n_samples))
    print "Best parameters found in CV:", gs.best_params_

    # clf = LogisticRegression(class_weight='balanced', C=50000)
    # fitted_model = clf.fit(m, targets.reshape(n_samples))

    predicted = fitted_model.predict_proba(m)
    predicted = predicted[:, 1]  # we're interested in probs for class 1

    # predicted = cross_validation.cross_val_predict(
    #     clf, m, targets.reshape(n_samples), cv=skf)
    print targets[:5], predicted[:5]

    predicted = gs.predict(m)
    print sum(predicted), sum(predicted - targets)
    print metrics.classification_report(targets, predicted)
    print metrics.f1_score(targets, predicted)
    print metrics.accuracy_score(targets, predicted)

    sys.exit()

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

    sys.exit()

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

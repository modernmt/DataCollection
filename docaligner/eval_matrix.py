#!/usr/bin/env python
# -*- coding: utf-8 -*-
from datetime import datetime
import dlib
import gzip
import json
import numpy as np
import sys


def read_devset(fh, mapping):
    # format fr-url <TAB> en-url
    devset = set()
    # print "Reading devset from ", fh.name
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
    parser.add_argument('-matrix',
                        help='read prediction/feature matrix',
                        type=argparse.FileType('r'), required=True)
    parser.add_argument('-matching',
                        help='compute max-cost matching',
                        action='store_true')
    parser.add_argument('-prefix',
                        help='output prefix (domain name)',
                        default="PREFIX")

    args = parser.parse_args(sys.argv[1:])

    url_mapping = read_idx2url(args.idx2url)
    devset = read_devset(args.devset, url_mapping)
    print "Loaded %d expected pairs from %s" % (len(devset), args.devset.name)

    fh = args.matrix
    if fh.name.endswith('.gz'):
        fh = gzip.GzipFile(fileobj=fh, mode='r')
    score_matrix = np.load(fh).astype(np.float32, copy=False)

    n_source, n_target = score_matrix.shape
    n_samples = n_source * n_target

    print "%d source / %d target docs" \
        % (n_source, n_target)

    print datetime.now()
    if args.matching:
        print "Finding best matching"
        matching_pairs = set()

        full_matrix = np.pad(
            score_matrix,
            ((0, max(score_matrix.shape) - score_matrix.shape[0]),
             (0, max(score_matrix.shape) - score_matrix.shape[1])),
            mode='constant')

        cost = dlib.matrix(full_matrix)
        print "Searching with dlib"
        assignment = dlib.max_cost_assignment(cost)

        for sidx, tidx in enumerate(assignment):
            if sidx >= score_matrix.shape[0] or tidx >= score_matrix.shape[1]:
                continue
            matching_pairs.add((sidx, tidx))

        print "Found %d matches " % (len(matching_pairs))
        found = devset.intersection(matching_pairs)
        print "Found %d out of %d pairs = %f%%" \
            % (len(found), len(devset), 100. * len(found) / len(devset))
        print "RES:\t%s\t%s\t%d\t%d" % (args.prefix, args.matrix.name,
                                        len(found), len(devset))
    else:
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
        found = devset.intersection(matches)
        print "Found %d out of %d pairs = %f%%" \
            % (len(found), len(devset), 100. * len(found) / len(devset))

        print "RES:\t%s\t%s\t%d\t%d" % (args.prefix, args.matrix.name,
                                        len(found), len(devset))

    print datetime.now()

    sys.exit()

    print "Finding best match (greedy)"
    greedy_matches = set()
    correct, errors = [], []
    # score_matrix = features[-1]
    # np.savetxt("scores", score_matrix)
    for s_idx in range(n_source):
        t_idx = np.argmax(score_matrix[s_idx])
        greedy_matches.add((s_idx, t_idx))

    # devset = set(devset.items())
    # print devset
    found = devset.intersection(greedy_matches)
    print "Found %d matches " % (len(greedy_matches))
    print "Found %d out of %d pairs = %f%%" \
        % (len(found), len(devset), 100. * len(found) / len(devset))

    print "Finding best match (greedy / restricted)"
    matches = set()
    correct, errors = [], []
    score_copy = score_matrix.copy()
    score_copy -= np.min(score_copy)
    while True:
        am = np.argmax(score_copy)
        am_row = am / score_copy.shape[1]
        am_col = am % score_copy.shape[1]
        if score_copy[am_row, am_col] <= 0:
            break
        matches.add((am_row, am_col))
        score_copy[am_row, :] = 0
        score_copy[:, am_col] = 0

        # if len(matches) >= min(n_source, n_target):
        #     break

    print "Found %d matches " % (len(matches))
    # print greedy_matches
    found = devset.intersection(matches)
    print "Found %d out of %d pairs = %f%%" \
        % (len(found), len(devset), 100. * len(found) / len(devset))

    result_greedy = len(found)
    #

    print "Finding best matching"
    matching_pairs = set()

    full_matrix = np.pad(
        score_matrix,
        ((0, max(score_matrix.shape) - score_matrix.shape[0]),
         (0, max(score_matrix.shape) - score_matrix.shape[1])),
        mode='constant')

    # print full_matrix.shape, np.sum(full_matrix)
    # print score_matrix.shape, np.sum(score_matrix)

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
    result_matching = len(found)
    print "RESULT\t%s\t%d\t%d\t%d" % (args.matrix.name, len(devset),
                                      result_greedy, result_matching)

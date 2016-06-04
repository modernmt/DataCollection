#!/usr/bin/env python
from __future__ import print_function

import sys
from hashlib import sha1
import numpy as np
np.random.seed(1337)  # for reproducibility
from collections import defaultdict
from itertools import izip
from scipy.spatial import distance
from scipy.stats import pearsonr, spearmanr

from keras.models import Sequential
from keras.layers.core import Dense, Dropout, Activation
from keras.layers.normalization import BatchNormalization
from keras.utils import np_utils
from keras.preprocessing.text import Tokenizer
from keras.layers.advanced_activations import PReLU, LeakyReLU
from keras.callbacks import Callback
from keras.optimizers import SGD

import mmh3

# salts = ["a", "b", "c", "d", "e", "f", "g", "h"]  # more secure than debian


def hashfunc(salt):
    h = sha1()
    h.update(salt)
    return h


def ngrams(sentence, order=1, vocab=None, sep='#'):
    for n in range(1, order + 1):
        if n == 2:
            sentence.insert(0, '<s>')
            sentence.append('</s>')
        for i in range(len(sentence) - n + 1):
            ngram_words = sentence[i:i + n]
            skip = False
            for w in ngram_words:
                if vocab and w not in vocab:
                    skip = True
                    break
            if not skip:
                yield sep.join(ngram_words)


def hash_line(line, n, size, order=1):
    line = line.strip().lower().split()
    res = []
    for w in ngrams(line, order):
        h1, h2 = mmh3.hash64(w)
        for s in range(n):
            hashval = (h1 + s * h2) % size
            res.append(int(hashval))
        # res.append(hash("%s\t%s" % (s, w)) % size)
    res = list(set(res))
    res.sort()
    # print ("%d => %d" %(len(line), len(res)))
    return res


def _read_corpus(args):
    source_corpus, target_corpus = [], []
    for line in args.train:
        s, t = line.split(' ||| ')
        s = hash_line(s, args.n, args.size, args.order)
        source_corpus.append(s)

        t = hash_line(t, args.n, args.size, args.order)
        target_corpus.append(t)
    return source_corpus, target_corpus


def sparse_to_dense(sparse_matrix, max_idx):
    m = np.zeros((len(sparse_matrix), max_idx),
                 dtype=np.float32)
    for i in range(len(sparse_matrix)):
        for j in sparse_matrix[i]:
            m[i, j] = 1
        # m[i] /= sum(m[i])
    return m.astype('float32')


def read_corpus(args):
    source_corpus, target_corpus = _read_corpus(args)
    # n_examples = len(source_corpus)

    print("First source: ", source_corpus[0][:10])
    print("First target: ", target_corpus[0][:10])

    X_train = sparse_to_dense(source_corpus, args.size)
    # X_test = sparse_to_dense(source_corpus[:n_test], args.size)
    print('X_train shape:', X_train.shape, "active:",
          sum(sum(X_train)) / X_train.size)
    # print('X_test shape:', X_test.shape)

    # Y_train = tokenizer.sequences_to_matrix(
    #     target_corpus[n_test:], mode="binary")
    # Y_test = tokenizer.sequences_to_matrix(
    #     target_corpus[:n_test], mode="binary")
    Y_train = sparse_to_dense(target_corpus, args.size)
    # Y_test = sparse_to_dense(target_corpus[:n_test], args.size)
    print('Y_train shape:', Y_train.shape, "active:",
          sum(sum(Y_train)) / Y_train.size)
    # print("First target mapped: ", Y_train[0][:10])

    return X_train, Y_train
    # return X_train, X_test, X_train, X_test


class EvalCorrelation(Callback):

    def __init__(self, args):
        # self.target_vocab = set(["<s>", "</s>"])
        self.read_eval(args)
        self.read_test(args)
        self.prefix = None
        if args.prefix:
            self.prefix = args.prefix
        self.history = defaultdict(list)
        self.writepred = args.writepred

    def read_test(self, args):
        source_corpus, target_corpus = [], []
        for line in open(args.test):
            source, target = line.split("\t")
            source_corpus.append(
                hash_line(source, args.n, args.size, args.order))
            target_corpus.append(
                hash_line(target, args.n, args.size, args.order))
        self.X_test = sparse_to_dense(source_corpus, args.size)
        self.Y_test = sparse_to_dense(target_corpus, args.size)
        print('X_test shape:', self.X_test.shape, "active:",
              np.sum(self.X_test) / self.X_test.size)
        print('Y_test shape:', self.Y_test.shape, "active:",
              np.sum(self.Y_test) / self.Y_test.size)

    def read_eval(self, args):
        source_corpus, target_corpus, self.scores = [], [], []
        for line in open(args.eval):
            source, target, score = line.split("\t")
            source_corpus.append(
                hash_line(source, args.n, args.size, args.order))
            target_corpus.append(
                hash_line(target, args.n, args.size, args.order))
            # for w in target.strip().split():
            #     self.target_vocab.add(w)
            self.scores.append(float(score))
        # self.X_eval = tokenizer.sequences_to_matrix(
        #     source_corpus, mode="binary")
        # self.Y_eval = tokenizer.sequences_to_matrix(
        #     target_corpus, mode="binary")
        self.X_eval = sparse_to_dense(source_corpus, args.size)
        self.Y_eval = sparse_to_dense(target_corpus, args.size)
        print('X_eval shape:', self.X_eval.shape, "active:",
              np.sum(self.X_eval) / self.X_eval.size)
        print('Y_eval shape:', self.Y_eval.shape, "active:",
              np.sum(self.Y_eval) / self.Y_eval.size)
        self.good = self.scores.count(1.0)
        print('Good (class 1) examples: ', self.good)

    # def get_target_vocab(self):
    #     return self.target_vocab

    def pos_prob(self, x, y):
        # return sum(np.log(x[y > 0])) / sum(y)
        pos_probs = np.log(x[y > 0])
        pos_probs = np.nan_to_num(pos_probs)
        return sum(pos_probs)

    def min_prob(self, x, y):
        """ the minimum probability of those fields, that should have
        been > .5 """
        return min(x[y > 0])

    def max_prob(self, x, y):
        """ maximum of those that should be zero """
        return max(x[y < 1])

    def all_prob(self, x, y):
        # return sum(np.log(x[y > 0])) / sum(y)
        pos_probs = np.log(x[y > 0])
        pos_probs[np.isnan(pos_probs)] = 0
        # pos_probs = np.nan_to_num(pos_probs)
        neg_probs = np.log(1 - x[y < 1])
        neg_probs[np.isnan(neg_probs)] = 0
        # neg_probs = np.nan_to_num(neg_probs)
        return sum(pos_probs) + sum(neg_probs)

    def count_correct(self, x, y):
        return sum((x > .5) == y) / sum(y)

    def print_score(self, probs, dist_func, name):
        dist = [dist_func(a, b) for a, b in izip(probs, self.Y_eval)]
        print(dist[0], self.scores[0], dist[1100],
              self.scores[1100], dist[-1], self.scores[-1])
        pearson, p = pearsonr(self.scores, dist)
        spearman, p = spearmanr(self.scores, dist)
        print ("[%s]\tP: %f\tS: %f\tSum: %f" %
               (name, pearson, spearman, sum(dist)))
        self.history[name].append((pearson, spearman, sum(dist)))

    def write_pred(self, model):
        probs = model.predict(self.X_test)
        if self.writepred:
            fh = open(self.writepred, 'w')
            np.savez(fh, X=self.X_test, Y=self.Y_test, predicted=probs)
            fh.close()

        if self.prefix:
            for f, n in (
                (distance.cosine, "Cosine"),
                (distance.euclidean, "Eulidean"),
                # (distance.correlation, "Correlation"),
                # (distance.braycurtis, "Bray-Curtis"),
                # (distance.canberra, "Canberra"),
                # (distance.chebyshev, "Chebyshev"),
                #  (distance.mahalanobis, "Mahalanobis"),
                # (distance.matching, "Matching"),
                # (distance.russellrao, "Russelrao"),
                (self.pos_prob, "PosProb", ),
                (self.all_prob, "AllProb"),
                # (self.min_prob, "MinProb"),
                (self.max_prob, "MaxProb"),
                (self.count_correct, "CorrectPercent")
            ):
                fh = open("%s_%s" % (self.prefix, n), 'w')
                dist = [f(a, b) for a, b in izip(probs, self.Y_test)]
                fh.write("\n".join(map(str, dist)))
                fh.write("\n")
                fh.close()

    def eval_model(self, model):
        # probs = model.predict_proba(self.X_eval)
        probs = model.predict(self.X_eval)
        assert probs.shape == self.Y_eval.shape

        print('')

        for f, n in (
            (distance.cosine, "Cosine"),
            (distance.euclidean, "Eulidean"),
            # (distance.correlation, "Correlation"),
            # (distance.braycurtis, "Bray-Curtis"),
            # (distance.canberra, "Canberra"),
            # (distance.chebyshev, "Chebyshev"),
            #  (distance.mahalanobis, "Mahalanobis"),
            # (distance.matching, "Matching"),
            # (distance.russellrao, "Russelrao"),
            (self.pos_prob, "PosProb", ),
            (self.all_prob, "AllProb"),
            (self.min_prob, "MinProb"),
            (self.max_prob, "MaxProb"),
            (self.count_correct, "CorrectPercent")
        ):
            self.print_score(probs, f, n)
            # try:
            #     self.print_score(probs, f, n)
            # except ValueError:
            #     continue

        # print ("Predicted:", sum(sum(probs > .5)))

    def on_epoch_end(self, epoch, logs={}):
        self.eval_model(self.model)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-size', help='size of bitarray',
                        type=int, default=1024)
    parser.add_argument('-batchsize', help='training batch size',
                        type=int, default=64)
    parser.add_argument('-layers', help='array of layer sizes',
                        type=int, nargs='+', default=[512])
    parser.add_argument('-activation',
                        help='activation for all but last layer',
                        default='relu')
    parser.add_argument('-train', type=argparse.FileType('r'),
                        help='training corpus in fastalign format',
                        required=True)
    parser.add_argument('-eval',
                        help='eval corpus in src<TAB>tgt<TAB>score format',
                        required=True)
    parser.add_argument('-prefix',
                        help='prefix for feature files')
    parser.add_argument('-test',
                        help='test corpus in src<TAB>tgt format',
                        required=True)
    parser.add_argument('-n', help='number of hash functions (default 5)',
                        type=int, default=5)
    parser.add_argument('-epochs', help='number of training iterations',
                        type=int, default=50)
    parser.add_argument('-order', help='order of n-grams (default 1)',
                        type=int, default=1)
    parser.add_argument('-dropout', help='amount of dropout in each layer',
                        type=float, default=0.3)
    parser.add_argument('-testpercent',
                        help='percent of train data to use as test',
                        type=int, default=0)
    parser.add_argument('-writepred', help='output file for predictions')
    args = parser.parse_args(sys.argv[1:])

    print("Commandline: ", " ".join(sys.argv))

    print("Building model...")
    model = Sequential()
    print ("layer sizes: %s" %
           ("-".join(
               [str(args.size)] + map(str, args.layers) + [str(args.size)])))

    for lid, layer_size in enumerate(args.layers):
        if lid == 0:
            model.add(Dense(output_dim=layer_size,
                            input_shape=(args.size,)))
        else:
            model.add(Dense(output_dim=layer_size))

        if args.activation.lower() == "prelu":
            model.add(PReLU())
        elif args.activation.lower() == "leakyrelu":
            model.add(LeakyReLU())
        else:
            model.add(Activation(args.activation))
        model.add(Dropout(0.3))

    model.add(Dense(args.size))
    model.add(Activation('sigmoid'))
    # sgd = SGD(lr=0.01, decay=1e-6, momentum=0.9, nesterov=True)
    # model.compile(loss='binary_crossentropy', optimizer=sgd)
    model.compile(loss='binary_crossentropy', optimizer='adam')
    # model.compile(loss='binary_crossentropy', optimizer='rmsprop')
    # model.compile(loss='mean_squared_error', optimizer='adam')
    # model.compile(loss='hinge', optimizer='adam')
    # model.compile(loss='cosine_proximity', optimizer='adam')

    print("Building evaluator ...")
    evaluator = EvalCorrelation(args)
    evaluator.eval_model(model)

    # Read corpus
    # X_train, X_test, Y_train, Y_test = read_corpus(
    #     args, evaluator.get_target_vocab())
    print("Reading corpus ...")
    X_train, Y_train = read_corpus(args)
    print("X_train shape: %s, Nonzero: %d" % (X_train.shape, np.sum(X_train)))

    print("Training model...")
    proba = model.predict(X_train, batch_size=args.batchsize)
    print(proba[0][:10])
    # print((proba[0] > 0.5 == Y_train[0])[:10])
    history = model.fit(X_train, Y_train, nb_epoch=args.epochs,
                        batch_size=args.batchsize, shuffle=False,
                        verbose=2,
                        validation_data=(evaluator.X_eval[:evaluator.good],
                                         evaluator.Y_eval[:evaluator.good]),
                        callbacks=[evaluator])

    evaluator.eval_model(model)
    evaluator.write_pred(model)

    proba = model.predict(X_train, batch_size=args.batchsize, verbose=0)
    print(proba[0][:10])
    print(Y_train[0][:10])
    # print((proba[0] > 0.5 == Y_train[0])[:10])
    # score = model.evaluate(
    #     X_test, Y_test, batch_size=args.batchsize, verbose=1)
    # print('Test score:', score)

    print(history.history['loss'])
    print(history.history['val_loss'])
    for k, v in evaluator.history.items():
        print(k, v)
    sys.exit()

#!/usr/bin/env python
from __future__ import print_function

import sys
from hashlib import sha1
import numpy as np
np.random.seed(1337)  # for reproducibility
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
salts = ["a", "b", "c", "d", "e", "f", "g", "h"]  # more secure than debian


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


def hash_line(line, salts, n, size, order=1, vocab=None):
    line = line.strip().lower().split()
    res = []
    for w in ngrams(line, order, vocab):
        for s in salts[:n]:
            # h = hashfunc(s)
            # h.update(w)
            # res.append(int(int(h.hexdigest(), 16) % size))
            res.append(hash("%s\t%s" % (s, w)) % size)
    res = list(set(res))
    res.sort()
    # print ("%d => %d" %(len(line), len(res)))
    return res


def _read_corpus(args, target_vocab):
    source_corpus, target_corpus = [], []
    for line in args.train:
        s, t = line.split(' ||| ')
        s = hash_line(s, salts, args.n, args.size, args.order)
        t = hash_line(t, salts, args.n, args.size, args.order, target_vocab)
        source_corpus.append(s)
        target_corpus.append(t)
    return source_corpus, target_corpus


def sparse_to_dense(sparse_matrix, max_idx):
    m = np.zeros((len(sparse_matrix), max_idx))
    for i in range(len(sparse_matrix)):
        for j in sparse_matrix[i]:
            m[i, j] = 1
        # m[i] /= sum(m[i])
    return m


def read_corpus(args, target_vocab):
    source_corpus, target_corpus = _read_corpus(args, target_vocab)
    n_examples = len(source_corpus)
    n_test = n_examples / 10

    print("First source: ", source_corpus[n_test][:10])
    print("First target: ", target_corpus[n_test][:10])

    X_train = sparse_to_dense(source_corpus[n_test:], args.size)
    X_test = sparse_to_dense(source_corpus[:n_test], args.size)
    print('X_train shape:', X_train.shape, "active:",
          sum(sum(X_train)) / X_train.size)
    print('X_test shape:', X_test.shape)

    # Y_train = tokenizer.sequences_to_matrix(
    #     target_corpus[n_test:], mode="binary")
    # Y_test = tokenizer.sequences_to_matrix(
    #     target_corpus[:n_test], mode="binary")
    Y_train = sparse_to_dense(target_corpus[n_test:], args.size)
    Y_test = sparse_to_dense(target_corpus[:n_test], args.size)
    print('Y_train shape:', Y_train.shape, "active:",
          sum(sum(Y_train)) / Y_train.size)
    print("First target mapped: ", Y_train[0][:10])
    print('Y_test shape:', Y_test.shape)

    return X_train, X_test, Y_train, Y_test
    # return X_train, X_test, X_train, X_test


class EvalCorrelation(Callback):

    def __init__(self, args):
        self.target_vocab = set(["<s>", "</s>"])
        self.read_eval(args)

    def read_eval(self, args):
        if not args.test:
            return
        source_corpus, target_corpus, self.scores = [], [], []
        for line in open(args.test):
            source, target, score = line.split("\t")
            source_corpus.append(
                hash_line(source, salts, args.n, args.size, args.order))
            target_corpus.append(
                hash_line(target, salts, args.n, args.size, args.order))
            for w in target.strip().split():
                self.target_vocab.add(w)
            self.scores.append(float(score))
        # self.X_eval = tokenizer.sequences_to_matrix(
        #     source_corpus, mode="binary")
        # self.Y_eval = tokenizer.sequences_to_matrix(
        #     target_corpus, mode="binary")
        self.X_eval = sparse_to_dense(source_corpus, args.size)
        self.Y_eval = sparse_to_dense(target_corpus, args.size)

    def get_target_vocab(self):
        return self.target_vocab

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
        return max(x[y < 1])

    def all_prob(self, x, y):
        # return sum(np.log(x[y > 0])) / sum(y)
        pos_probs = np.log(x[y > 0])
        pos_probs = np.nan_to_num(pos_probs)
        neg_probs = np.log(1 - x[y < 1])
        neg_probs = np.nan_to_num(neg_probs)
        return sum(pos_probs) + sum(neg_probs)

    def count_correct(self, x, y):
        return sum((x > .5) == y) / sum(y)

    def print_score(self, probs, dist_func, name):
        dist = [dist_func(a, b) for a, b in zip(probs, self.Y_eval)]
        pearson, p = pearsonr(self.scores, dist)
        spearman, p = spearmanr(self.scores, dist)
        print ("[%s] Sum: %f\tP: %f\tS: %f" %
               (name, sum(dist), pearson, spearman))

    def eval_model(self, model):
        # probs = model.predict_proba(self.X_eval)
        probs = model.predict(self.X_eval)
        assert probs.shape == self.Y_eval.shape

        for f, n in ((distance.cosine, "Cosine"),
                     (distance.euclidean, "Eulidean"),
                     (distance.correlation, "Correlation"),
                     (distance.braycurtis, "Bray-Curtis"),
                     (distance.canberra, "Canberra"),
                     (distance.chebyshev, "Chebyshev"),
                    #  (distance.mahalanobis, "Mahalanobis"),
                     (distance.matching, "Matching"),
                     (distance.russellrao, "Russelrao"),
                     (self.pos_prob, "PosProb", ),
                     (self.all_prob, "AllProb"),
                     (self.min_prob, "MinProb"),
                     (self.max_prob, "MaxProb"),
                     (self.count_correct, "CorrectPercent")):
            self.print_score(probs, f, n)

        print ("Predicted:", sum(sum(probs > .5)))

    def on_epoch_end(self, epoch, logs={}):
        self.eval_model(self.model)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-size', help='size of bitarray',
                        type=int, default=100)
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
    parser.add_argument('-test',
                        help='test corpus in src<TAB>tgt<TAB>score format',
                        required=True)
    parser.add_argument('-n', help='number of hash functions (default 5)',
                        type=int, default=5)
    parser.add_argument('-epochs', help='number of training iterations',
                        type=int, default=50)
    parser.add_argument('-order', help='order of n-grams (default 1)',
                        type=int, default=1)
    args = parser.parse_args(sys.argv[1:])

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
        model.add(Dropout(0.5))

    model.add(Dense(args.size))
    model.add(Activation('sigmoid'))
    # sgd = SGD(lr=0.1, decay=1e-6, momentum=0.9, nesterov=True)
    # model.compile(loss='binary_crossentropy', optimizer=sgd)
    model.compile(loss='binary_crossentropy', optimizer='adam')
    # model.compile(loss='binary_crossentropy', optimizer='rmsprop')
    # model.compile(loss='categorical_crossentropy', optimizer='adam')
    # model.compile(loss='mean_squared_error', optimizer='adam')
    # model.compile(loss='hinge', optimizer='adam')
    # model.compile(loss='categorical_crossentropy', optimizer='adam')
#
    # model.compile(loss='mean_squared_error', optimizer='adam')

    evaluator = EvalCorrelation(args)
    evaluator.eval_model(model)

    # Read corpus
    # X_train, X_test, Y_train, Y_test = read_corpus(
    #     args, evaluator.get_target_vocab())
    X_train, X_test, Y_train, Y_test = read_corpus(
        args, None)

    print("Training model...")
    proba = model.predict(X_train, batch_size=args.batchsize)
    print(proba[0][:10])
    # print((proba[0] > 0.5 == Y_train[0])[:10])
    history = model.fit(X_train, Y_train, nb_epoch=args.epochs,
                        batch_size=args.batchsize, shuffle=True,
                        verbose=1, validation_split=0.1,
                        callbacks=[evaluator])

    proba = model.predict(X_train, batch_size=args.batchsize, verbose=0)
    print(proba[0][:10])
    # print((proba[0] > 0.5 == Y_train[0])[:10])
    score = model.evaluate(
        X_test, Y_test, batch_size=args.batchsize, verbose=1)
    print('Test score:', score)

    # print(history.history['loss'])
    # print(history.history['val_loss'])
    sys.exit()

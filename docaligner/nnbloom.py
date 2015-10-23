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
salts = ["a", "b", "c", "d", "e", "f", "g", "h"]  # more secure than debian


def hashfunc(salt):
    h = sha1()
    h.update(salt)
    return h


def ngrams(sentence, order=1, sep='#'):
    for n in range(1, order + 1):
        prefix = ''
        if n > 1:
            sentence.insert(0, '<s>')
            sentence.append('</s>')
        for i in range(len(sentence) - n + 1):
            yield prefix + sep.join(sentence[i:i + n])


def hash_line(line, salts, n, size, order=1):
    line = line.strip().split()
    res = []
    for w in ngrams(line, order):
        for s in salts[:n]:
            h = hashfunc(s)
            h.update(w)
            res.append(int(int(h.hexdigest(), 16) % size))
    res = list(set(res))
    res.sort()
    return res


def _read_corpus(args):
    source_corpus, target_corpus = [], []
    for line in args.train:
        s, t = line.split(' ||| ')
        s = hash_line(s, salts, args.n, args.size, args.order)
        t = hash_line(t, salts, args.n, args.size, args.order)
        source_corpus.append(s)
        target_corpus.append(t)
    return source_corpus, target_corpus


def sparse_to_dense(sparse_matrix, max_idx):
    m = np.zeros((len(sparse_matrix), max_idx))
    for i in range(len(sparse_matrix)):
        for j in sparse_matrix[i]:
            m[i, j] = 1
    return m


def read_corpus(args):
    source_corpus, target_corpus = _read_corpus(args)
    n_examples = len(source_corpus)
    n_test = n_examples / 10

    print(source_corpus[n_test])
    print(target_corpus[n_test])

    print("Vectorizing sequence data...")

    # tokenizer = Tokenizer(args.size)
    # X_train = tokenizer.sequences_to_matrix(
    #     source_corpus[n_test:], mode="binary")
    # X_test = tokenizer.sequences_to_matrix(
    #     source_corpus[:n_test], mode="binary")
    X_train = sparse_to_dense(source_corpus[n_test:], args.size)
    X_test = sparse_to_dense(source_corpus[:n_test], args.size)
    print('X_train shape:', X_train.shape)
    print('X_test shape:', X_test.shape)

    # Y_train = tokenizer.sequences_to_matrix(
    #     target_corpus[n_test:], mode="binary")
    # Y_test = tokenizer.sequences_to_matrix(
    #     target_corpus[:n_test], mode="binary")
    Y_train = sparse_to_dense(target_corpus[n_test:], args.size)
    Y_test = sparse_to_dense(target_corpus[:n_test], args.size)
    print('Y_train shape:', Y_train.shape)
    print(Y_train[0])
    print('Y_test shape:', Y_test.shape)

    return X_train, X_test, Y_train, Y_test


class EvalCorrelation(Callback):

    def __init__(self, args):
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
            self.scores.append(float(score))
        # self.X_eval = tokenizer.sequences_to_matrix(
        #     source_corpus, mode="binary")
        # self.Y_eval = tokenizer.sequences_to_matrix(
        #     target_corpus, mode="binary")
        self.X_eval = sparse_to_dense(source_corpus, args.size)
        self.Y_eval = sparse_to_dense(target_corpus, args.size)

    def eval_model(self, model):
        probs = model.predict_proba(self.X_eval)
        dist = [distance.cosine(a, b) for a, b in zip(probs, self.Y_eval)]
        r, p = pearsonr(self.scores, dist)
        print ("Pearson's r:\t", r)
        r, p = spearmanr(self.scores, dist)
        print ("Spearmans's r:\t", r)
        dist = [distance.euclidean(a, b) for a, b in zip(probs, self.Y_eval)]
        r, p = pearsonr(self.scores, dist)
        print ("Pearson's r:\t", r)
        r, p = spearmanr(self.scores, dist)
        print ("Spearmans's r:\t", r)
        dist = [sum((a > .5) == b) for a, b in zip(probs, self.Y_eval)]
        print ("Correct:", sum(dist))

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
    parser.add_argument('-o', action='store', dest='order',
                        help='order of n-grams (default 1)',
                        type=int, default=1)
    args = parser.parse_args(sys.argv[1:])

    # Read corpus
    X_train, X_test, Y_train, Y_test = read_corpus(args)

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
        elif args.activation.lower() == "leakyrelU":
            model.add(LeakyReLU())
        else:
            model.add(Activation(args.activation))
        model.add(Dropout(0.5))

    model.add(Dense(args.size))
    model.add(Activation('sigmoid'))
    model.compile(loss='binary_crossentropy', optimizer='adam')

    evaluator = EvalCorrelation(args)
    evaluator.eval_model(model)

    print("Training model...")
    proba = model.predict_proba(X_train, batch_size=args.batchsize)
    print(proba[0])
    history = model.fit(X_train, Y_train, nb_epoch=args.epochs,
                        batch_size=args.batchsize, shuffle=True,
                        verbose=1, validation_split=0.1,
                        callbacks=[evaluator])

    proba = model.predict_proba(X_train, batch_size=args.batchsize, verbose=0)
    print(proba[0])
    score = model.evaluate(
        X_test, Y_test, batch_size=args.batchsize, verbose=1)
    print('Test score:', score)

    # print(history.history['loss'])
    # print(history.history['val_loss'])
    sys.exit()

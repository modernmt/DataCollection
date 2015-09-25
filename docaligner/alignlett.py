#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from collections import namedtuple, defaultdict
from HTMLParser import HTMLParser
import difflib
import threading
import base64
import numpy as np
import lxml.html
import subprocess
import os
import math
from functools import partial
from urlparse import urljoin
from nltk.align import gale_church
from nltk.tokenize.punkt import PunktSentenceTokenizer

# For simhash Distance
from simhash import Simhash

# for Hungarian Algorithm
import munkres

sys.path.append("/home/buck/net/build/DataCollection/baseline")
from strip_language_from_uri import LanguageStripper

Page = namedtuple("Page", "url, html, text, mime_type, encoding")

# for Named Entity Annotation
import jsonrpclib
import json
# from corenlp import StanfordCoreNLP


class SpaceTokenizer(object):

    """ Fall-back is no tokenizer is available """

    def __init__(self):
        sys.stderr.write("Using SpaceTokenizer.\n")

    def process(self, line):
        return line.split()


class ExternalProcessor(object):

    """ wraps an external script and does utf-8 conversions, is thread-safe """

    def __init__(self, cmd):
        self.cmd = cmd
        self.devnull = open(os.devnull, 'wb')
        if self.cmd is not None:
            self.proc = subprocess.Popen(cmd.split(), stdin=subprocess.PIPE,
                                         stdout=subprocess.PIPE,
                                         stderr=self.devnull)
            self._lock = threading.Lock()

    def process(self, line):
        if self.cmd is None or not line.strip():
            return line
        u_string = u"%s\n" % line
        u_string = u_string.encode("utf-8")
        result = u_string  # fallback: return input
        with self._lock:
            self.proc.stdin.write(u_string)
            self.proc.stdin.flush()
            result = self.proc.stdout.readline()
        return result.decode("utf-8").strip()


class DistanceScorer(object):

    def __init__(self):
        self.name = "Default Distance Scorer"
        self._threadsafe = False

    def __str__(self):
        return self.name

    def _score_pair(self, s_idx, s_page, t_idx, t_page):
        """ Overwrite this with you distance of choice """
        return 0

    def _extract(self, source_corpus, target_corpus):
        """ This is called before scoring of pairs. Overwrite to extract const
        data """
        pass

    def score(self, source_corpus, target_corpus):
        self._extract(source_corpus, target_corpus)
        sys.stderr.write("Done extracting...\n")
        scoring_matrix = np.zeros((len(source_corpus), len(target_corpus)))
        for s_idx, (s_url, s_page) in enumerate(s.iteritems()):
            for t_idx, (t_url, t_page) in enumerate(t.iteritems()):
                scoring_matrix[s_idx, t_idx] = self._score_pair(
                    s_idx, s_page, t_idx, t_page)
        sys.stderr.write("Done scoring...\n")
        return scoring_matrix


class LinkDistance(DistanceScorer):

    def __init__(self, xpath='//a/@href'):
        self.name = "Link Distance Scorer (xpath: %s)" % xpath
        self.t_links = []
        self.s_links = []
        self.xpath = xpath

    def _extract(self, source_corpus, target_corpus):
        for url, page in source_corpus.iteritems():
            self.s_links.append(
                self._extract_links(page.url, page.html.encode("utf-8")))
        for url, page in target_corpus.iteritems():
            self.t_links.append(
                self._extract_links(page.url, page.html.encode("utf-8")))

    def _score_pair(self, s_idx, s_page, t_idx, t_page):
        source_links = self.s_links[s_idx]
        target_links = self.t_links[t_idx]
        s = difflib.SequenceMatcher(None, source_links, target_links)
        return s.ratio()

    def _extract_links(self, url, html):
        dom = lxml.html.fromstring(html)
        links = []
        for link in dom.xpath(self.xpath):
            links.append(urljoin(url, link))
        return links


def read_lett(f, slang, tlang):
    s, t = {}, {}
    for line in f:
        lang, mine, enc, name, html, text = line.strip().split("\t")
        html = base64.b64decode(html).decode("utf-8")
        text = base64.b64decode(text).decode("utf-8")
        assert lang in [slang, tlang]
        p = Page(name, html, text, mine, enc)
        if lang == slang:
            s[name] = p
        else:
            t[name] = p
    return s, t


class NERDistance(DistanceScorer):

    """ Assuming source langauge is English """

    def __init__(self, location="http://localhost:8080",
                 source_tokenizer=None, target_tokenizer=None):
        self.name = "NamedEntity Distance Scorer"
        self.server = jsonrpclib.Server(location)
        self.s_entities = []
        self.source_tokenizer = source_tokenizer
        if not source_tokenizer:
            self.source_tokenizer = SpaceTokenizer()

        self.target_tokenizer = target_tokenizer
        if not target_tokenizer:
            self.target_tokenizer = SpaceTokenizer()

    def _extract_entities(self, text):
        entities = defaultdict(list)

        for line in text:
            try:
                parsed = json.loads(self.server.parse(line))
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                sys.stderr.write("Parsing failed: '%s'\n" %
                                 (line.encode("utf-8")))
                return entities

            # parsed = self.corenlp.raw_parse(text)
            # print parsed
            if not parsed:
                continue
            if "sentences" not in parsed:
                print parsed
                continue

            for s in parsed["sentences"]:
                for w, annotation in s["words"]:
                    ne_type = annotation.get("NamedEntityTag", 'O')
                    if ne_type != 'O':
                        # print w, ne_type
                        entities[ne_type].append(w)
        return entities

    def _extract(self, source_corpus, target_corpus):
        for idx, (url, page) in enumerate(source_corpus.iteritems()):
            valid_words = set()

            text = map(self.source_tokenizer.process, page.text.split("\n"))

            entities = self._extract_entities(text)

            for ne_type in entities:
                for w in entities[ne_type]:
                    valid_words.add(w)

            filtered_source = [
                w for w in "\n".join(text).split() if w in valid_words]
            # print filtered_source
            self.s_entities.append((entities, valid_words, filtered_source))

    def _score_pair(self, s_idx, s_page, t_idx, t_page):
        t_text = "\n".join(
            map(self.target_tokenizer.process, t_page.text.split("\n")))

        entities, valid_words, filtered_source = self.s_entities[s_idx]
        filtered_target = [w for w in t_text.split() if w in valid_words]

        s = difflib.SequenceMatcher(None, filtered_source, filtered_target)
        return s.ratio()


class BOWScorer(DistanceScorer):

    def __init__(self, source_tokenizer=None, target_tokenizer=None):
        self.name = "Bag of Words Scorer"
        self.sbow = []
        self.tbow = []

        self.source_tokenizer = source_tokenizer
        if not source_tokenizer:
            self.source_tokenizer = SpaceTokenizer()

        self.target_tokenizer = target_tokenizer
        if not target_tokenizer:
            self.target_tokenizer = SpaceTokenizer()

    def _words_from_text(self, text, tokenizer):
        words = set()
        for line in text.split("\n"):
            for w in line.lower().split():
                words.add(w)
        return words

    def _extract(self, source_corpus, target_corpus):
        for idx, (url, page) in enumerate(source_corpus.iteritems()):
            self.sbow.append(
                self._words_from_text(page.text, self.source_tokenizer))
        for idx, (url, page) in enumerate(target_corpus.iteritems()):
            self.tbow.append(
                self._words_from_text(page.text, self.target_tokenizer))

    def _jaccard(self, set1, set2):
        return float(len(set1.intersection(set2))) / len(set1.union(set2))

    def _score_pair(self, s_idx, s_page, t_idx, t_page):
        return self._jaccard(self.sbow[s_idx], self.tbow[t_idx])


def get_best_match(source_corpus, target_corpus, scores):
    stripper = LanguageStripper()
    err = 0
    for s_idx, (s_url, s_page) in enumerate(source_corpus.iteritems()):
        max_idx = np.argmax(scores[s_idx])
        t_url = target_corpus.keys()[max_idx]
        success = stripper.strip(t_url) == stripper.strip(s_page.url)
        if not success:
            err += 1
        sys.stdout.write("%f\t%s\t%s\t%s\n" %
                         (scores[s_idx, max_idx], success, s_url, t_url))
    n = min(len(source_corpus), len(target_corpus))
    sys.stderr.write("Correct (greedy): %d out of %d = %f%%\n" %
                     (n - err, n, (1. * n - err) / n))


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


def get_best_matching(source_corpus, target_corpus, scores):
    stripper = LanguageStripper()
    err = 0

    m = munkres.Munkres()
    cost_matrix = munkres.make_cost_matrix(scores, lambda cost: 1 - cost)
    indexes = m.compute(cost_matrix)

    for row, column in indexes:
        s_url = source_corpus.keys()[row]
        t_url = target_corpus.keys()[column]
        success = stripper.strip(t_url) == stripper.strip(s_url)
        if not success:
            err += 1
        sys.stdout.write("%f\t%s\t%s\t%s\n" %
                         (scores[row, column], success, s_url, t_url))

    n = min(len(source_corpus), len(target_corpus))
    sys.stderr.write("Correct: %d out of %d = %f%%\n" %
                     (n - err, n, (1. * n - err) / n))


class HTMLSequencer(HTMLParser):

    def __init__(self, length_function, growth_function):
        HTMLParser.__init__(self)
        self.sequence = []
        self.length_function = length_function
        self.growth_function = growth_function

    def handle_starttag(self, tag, attrs):
        self.sequence.append("<%s>" % tag)

    def handle_endtag(self, tag):
        self.sequence.append("</%s>" % tag)

    def handle_data(self, data):
        if not data.strip():
            return
        n = self.length_function(data)

        for n in range(self.growth_function(n)):
            self.sequence.append("%d" % n)

    def get_result(self):
        return self.sequence

    def reset(self):
        HTMLParser.reset(self)
        self.sequence = []


class StructureScorer(DistanceScorer):

    def __init__(self, length_function, growth_function, ratio_function):
        self.name = "Bag of Words Scorer"
        self.sseq = []
        self.tseq = []
        self.length_function = length_function
        self.growth_function = growth_function
        self.ratio_function = ratio_function

    def _html_to_sequence(self, html):
        parser = HTMLSequencer(self.length_function, self.growth_function)
        parser.feed(html)
        return parser.get_result()

    def _extract(self, source_corpus, target_corpus):
        for url, page in source_corpus.iteritems():
            self.sseq.append(self._html_to_sequence(page.html))
        for url, page in target_corpus.iteritems():
            self.tseq.append(self._html_to_sequence(page.html))

    def _score_pair(self, s_idx, s_page, t_idx, t_page):
        # if s_idx + t_idx == 0:
        #     print self.sseq[0]
        #     print self.tseq[0]
        #     d = difflib.Differ()
        #     print d.compare(self.sseq[s_idx], self.tseq[t_idx])
        #     s = difflib.SequenceMatcher(
        #         None, self.sseq[s_idx], self.tseq[t_idx])
        #     print s.ratio()
        #     s = difflib.SequenceMatcher(
        #         None, self.sseq[s_idx], self.tseq[t_idx])
        #     print s.quick_ratio()
        #     s = difflib.SequenceMatcher(
        #         None, self.sseq[s_idx], self.tseq[t_idx])
        #     print s.real_quick_ratio()

        return self.ratio_function(self.sseq[s_idx], self.tseq[t_idx])


class GaleChurchWrapper(object):

    def __init__(self):
        self.params = gale_church.LanguageIndependent
        self.alignment_types = list(self.params.PRIORS.keys())

    def align_score(self, source_sents, target_sents, max_dist=100):
        D = [[]]

        # backlinks = {}

        for i in range(len(source_sents) + 1):
            for j in range(len(target_sents) + 1):
                min_dist = float('inf')
                # min_align = None
                for a in self.alignment_types:
                    prev_i = - 1 - a[0]
                    prev_j = j - a[1]
                    if prev_i < -len(D) or prev_j < 0:
                        continue
                    p = D[prev_i][prev_j] + \
                        gale_church.align_log_prob(i, j,
                                                   source_sents, target_sents,
                                                   a, self.params)
                    if p < min_dist:
                        min_dist = p
                        # min_align = a

                if min_dist == float('inf'):
                    # return max_dist
                    min_dist = 0
                elif min_dist >= max_dist:
                    return max_dist

                # backlinks[(i, j)] = min_align
                D[-1].append(min_dist)

            if len(D) > 2:
                D.pop(0)
            D.append([])
        # print D
        # print backlinks
        # sys.exit()
        if D[-2][-1] == 0:
            return -max_dist
        return -D[-2][-1]


class GaleChurchAlignmentDistance(DistanceScorer):

    def __init__(self):
        self.gc = GaleChurchWrapper()
        self.name = "Gale Church Alignment Scorer"
        self.tokenizer = PunktSentenceTokenizer()
        self.sblocks, self.tblocks = [], []

    def _blocks_from_text(self, text):
        blocks = []
        for sentence in self.tokenizer.sentences_from_text(
                text.replace('\n', '')):
            blocks.append(len(sentence))
            # maybe count tokens? or non-spaces?
        return blocks

    def _extract(self, source_corpus, target_corpus):
        for url, page in source_corpus.iteritems():
            self.sblocks.append(self._blocks_from_text(page.text))
        for url, page in target_corpus.iteritems():
            self.tblocks.append(self._blocks_from_text(page.text))

    def _score_pair(self, s_idx, s_page, t_idx, t_page):
        return self.gc.align_score(self.sblocks[s_idx], self.tblocks[t_idx])


class SimhashDistance(DistanceScorer):

    def __init__(self, source_tokenizer, target_tokenizer, n=2):
        self.name = "Simhash Distance Scorer, n=%d" % n
        self.sentence_splitter = PunktSentenceTokenizer()
        self.s_hashes, self.t_hashes = [], []

        self.source_tokenizer = source_tokenizer
        if not source_tokenizer:
            self.source_tokenizer = SpaceTokenizer()

        self.target_tokenizer = target_tokenizer
        if not target_tokenizer:
            self.target_tokenizer = SpaceTokenizer()

        def ngrams(n, tokenizer, page):
            result = []
            text = page.text.replace('\n', '')
            for sentence in self.sentence_splitter.sentences_from_text(text):
                if not sentence.strip():
                    continue
                # if '\n' in sentence:
                #     print repr(sentence)
                assert '\n' not in sentence, sentence
                words = tokenizer.process(sentence).strip().split()
                result += [" ".join(words[i:i + n]) for i in
                           range(max(len(words) - n + 1, 1))]
            return result

        def tokens(n, tokenizer, page):
            # 180/1grams
            words = page.text.split()
            return [" ".join(words[i:i + n]) for i in
                    range(max(len(words) - n + 1, 1))]

        def chars(n, tokenizer, page):
            words = page.html.replace("\n", '')
            words = words.replace(" ", '')
            return [" ".join(words[i:i + n]) for i in
                    range(max(len(words) - n + 1, 1))]

        def html_tokens(n, tokenizer, page):
            # 153/trigrams
            words = page.html.split()
            return [" ".join(words[i:i + n]) for i in
                    range(max(len(words) - n + 1, 1))]

        # self.source_features = partial(ngrams, n, self.source_tokenizer)
        # self.target_features = partial(ngrams, n, self.target_tokenizer)
        # self.source_features = partial(tokens, n, self.source_tokenizer)
        # self.target_features = partial(tokens, n, self.target_tokenizer)
        self.source_features = partial(chars, n, self.source_tokenizer)
        self.target_features = partial(chars, n, self.target_tokenizer)
        # print self.source_features("How are you?\nI am fine. Thanks.")

    def _words_from_text(self, text, tokenizer):
        words = set()
        for line in self.sentence_splitter(text):
            for w in tokenizer.process(line).split("\n"):
                words.add(w)
        return words

    def _extract(self, source_corpus, target_corpus):
        for url, page in source_corpus.iteritems():
            self.s_hashes.append(Simhash(self.source_features(page)))
        for url, page in target_corpus.iteritems():
            self.t_hashes.append(Simhash(self.target_features(page)))

    def _score_pair(self, s_idx, s_page, t_idx, t_page):
        return -self.s_hashes[s_idx].distance(self.t_hashes[t_idx])

    def get_features(self, text):
        width = 3
        text = self.tokenizer.sentences_from_text(text)
        return [text[i:i + width] for i in
                range(max(len(text) - width + 1, 1))]


def ratio(seq1, seq2):
    s = difflib.SequenceMatcher(None, seq1, seq2)
    return s.ratio()


def quick_ratio(seq1, seq2):
    s = difflib.SequenceMatcher(None, seq1, seq2)
    return s.quick_ratio()


def real_quick_ratio(seq1, seq2):
    s = difflib.SequenceMatcher(None, seq1, seq2)
    return s.real_quick_ratio()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'lettfile', help='input lett file', type=argparse.FileType('r'))
    parser.add_argument('-slang', help='source language', default='en')
    parser.add_argument('-tlang', help='target language', default='fr')
    parser.add_argument(
        '-source_tokenizer', help='call to tokenizer, including arguments')
    parser.add_argument(
        '-target_tokenizer', help='call to tokenizer, including arguments')
    parser.add_argument(
        '-corenlp_service', help='corenlp json service location',
        default='http://localhost:8080')
    args = parser.parse_args(sys.argv[1:])

    # gc = GaleChurchWrapper()
    # print gc.align_score([15, 2, 2, 2, 2, 10], [12, 3, 20, 3, 12])
    # sys.exit()

    # read source and target corpus
    s, t = read_lett(args.lettfile, args.slang, args.tlang)
    sys.stderr.write("Read %d %s docs and %d %s docs from %s\n" %
                     (len(s), args.slang,
                      len(t), args.tlang, args.lettfile.name))

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

    source_tokenizer = ExternalProcessor(
        args.source_tokenizer) if args.source_tokenizer else SpaceTokenizer()
    target_tokenizer = ExternalProcessor(
        args.target_tokenizer) if args.target_tokenizer else SpaceTokenizer()

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

    distance_scorers = [StructureScorer(
        length_function=lambda x: len(x.split()),
        growth_function=lambda x: int(1 + math.log(x)),
        ratio_function=lambda x: quick_ratio),
        BOWScorer(source_tokenizer=source_tokenizer,
                  target_tokenizer=target_tokenizer),
        LinkDistance()]
    for scorer in distance_scorers:
        sys.stderr.write("Running: %s\n" % str(scorer))
        m = scorer.score(s, t)
        get_best_match(s, t, m)
        get_nbest(s, t, m, n=10)
        get_nbest(s, t, m, n=20)
        get_nbest(s, t, m, n=100)
        # get_best_matching(s, t, m)

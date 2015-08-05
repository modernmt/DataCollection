#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from collections import namedtuple, defaultdict
import difflib
import threading
import base64
import numpy as np
import lxml.html
import subprocess
from urlparse import urljoin

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
        if self.cmd is not None:
            self.proc = subprocess.Popen(cmd.split(), stdin=subprocess.PIPE,
                                         stdout=subprocess.PIPE)
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

    def __str__(self):
        return self.name

    def _score_pair(self, s_idx, s_page, t_idx, t_page):
        """ Overwrite this with you distance of choice """
        return 0

    def _extract(source_corpus, target_corpus):
        """ This is called before scoring of pairs. Overwrite to extract const data """
        pass

    def score(self, source_corpus, target_corpus):
        self._extract(source_corpus, target_corpus)
        scoring_matrix = np.zeros((len(source_corpus), len(target_corpus)))
        for s_idx, (s_url, s_page) in enumerate(s.iteritems()):
            for t_idx, (t_url, t_page) in enumerate(t.iteritems()):
                scoring_matrix[s_idx, t_idx] = self._score_pair(
                    s_idx, s_page, t_idx, t_page)
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

    # read source and target corpus
    s, t = read_lett(args.lettfile, args.slang, args.tlang)
    sys.stderr.write("Read %d %s docs and %d %s docs from %s\n" %
                     (len(s), args.slang,
                      len(t), args.tlang, args.lettfile.name))

    # distance_scorers = [LinkDistance(), LinkDistance(xpath="//img/@src")]
    source_tokenizer = ExternalProcessor(
        args.source_tokenizer) if args.source_tokenizer else SpaceTokenizer()
    target_tokenizer = ExternalProcessor(
        args.target_tokenizer) if args.target_tokenizer else SpaceTokenizer()

    distance_scorers = [BOWScorer(source_tokenizer=source_tokenizer,
                                  target_tokenizer=target_tokenizer),
                        LinkDistance(),
                        LinkDistance(xpath="//img/@src"),
                        # NERDistance(args.corenlp_service,
                        #             source_tokenizer=source_tokenizer,
                        #             target_tokenizer=target_tokenizer)
                        ]
    for scorer in distance_scorers:
        sys.stderr.write("Running: %s\n" % str(scorer))
        m = scorer.score(s, t)
        get_best_matching(s, t, m)
        get_best_match(s, t, m)

#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from collections import namedtuple
import difflib
import base64
import numpy as np
import lxml.html
from urlparse import urljoin

# for Hungarian Algorithm
import munkres

sys.path.append("/home/buck/net/build/DataCollection/baseline")
from strip_language_from_uri import LanguageStripper

Page = namedtuple("Page", "url, html, text, mime_type, encoding")

class DistanceScorer(object):

    def __init__(self):
        pass

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
        self.t_links = []
        self.s_links = []
        self.xpath = xpath

    def _extract(self, source_corpus, target_corpus):
        for url, page in source_corpus.iteritems():
            self.s_links.append(self._extract_links(page.url, page.html.encode("utf-8")))
        for url, page in target_corpus.iteritems():
            self.t_links.append(self._extract_links(page.url, page.html.encode("utf-8")))

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

def get_best_match(source_corpus, target_corpus, scores):
        stripper = LanguageStripper()
        err = 0
        for s_idx, (s_url, s_page) in enumerate(source_corpus.iteritems()):
            max_idx = np.argmax(scores[s_idx])
            t_url = target_corpus.keys()[max_idx]
            success = stripper.strip(t_url) == stripper.strip(s_page.url)
            if not success:
                err += 1
            print scores[s_idx, max_idx], success, s_page.url, t_url
        n = min(len(source_corpus), len(target_corpus))
        print "Correct: %d out of %d = %f%%" %(n-err, n, (1.*n-err)/n)

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
            print scores[row, column], success, s_url, t_url

        n = min(len(source_corpus), len(target_corpus))
        print "Correct: %d out of %d = %f%%" %(n-err, n, (1.*n-err)/n)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'lettfile', help='input lett file', type=argparse.FileType('r'))
    parser.add_argument('-slang', help='source language', default='en')
    parser.add_argument('-tlang', help='target language', default='fr')
    args = parser.parse_args(sys.argv[1:])

    # read source and target corpus
    s, t = read_lett(args.lettfile, args.slang, args.tlang)
    sys.stderr.write("Read %d %s docs and %d %s docs from %s\n" %
                     (len(s), args.slang,
                      len(t), args.tlang, args.lettfile.name))

    distance_scorers = [LinkDistance()]
    for scorer in distance_scorers:
        m = scorer.score(s, t)
        get_best_matching(s, t, m)
        # for url, (html, text, mine, enc) in s.iteritems():
        #     scorer._extract_links(url, html)
        #     break
        # break

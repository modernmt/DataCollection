from collections import defaultdict
from functools import partial
from nltk.align import gale_church
from nltk.tokenize.punkt import PunktSentenceTokenizer
from simhash import Simhash
from urlparse import urljoin
from functools import partial
import difflib
import json
import jsonrpclib
import lxml.html
import numpy as np
import re
import sys
import codecs
import multiprocessing


from tokenizer import SpaceTokenizer
from htmlprocessor import HTMLSequencer
from ratio import ratio
from itertools import izip_longest
from pathos.pools import ParallelPool as Pool


def ratio_pool(seqs2, ratio_function, seq1):
    rf = partial(ratio_function, seq1)
    return map(rf, seqs2)


def ngrams_from_text(n, _url, page):
    words = page.text.split()
    ngrams = [" ".join(words[i:i + n]) for i in
              range(max(len(words) - n + 1, 1))]
    return map(hash, ngrams)


class ExtractionMapper(object):

    def __init__(self, extraction_function=None, processes=1):
        self.ef = extraction_function
        self.processes = processes

    def extract(self, corpus):
        if self.processes > 1:
            p = multiprocessing.Pool()
            return [p.apply(self.ef, args=(url, page))
                    for url, page in corpus.iteritems()]
        else:
            return [self.ef(url, page)
                    for url, page in corpus.iteritems()]

    def extract_source(self, corpus):
        return self.extract(corpus)

    def extract_target(self, corpus):
        return self.extract(corpus)


class WordExtractor(ExtractionMapper):

    def __init__(self, n=1):
        super(WordExtractor, self).__init__(
            extraction_function=partial(ngrams_from_text, n))


class LinkExtractor(ExtractionMapper):

    def __init__(self, xpath):
        super(LinkExtractor, self).__init__(
            extraction_function=self._extract_links)
        self.xpath = xpath

    def _extract_links(self, url, page):
        dom = lxml.html.fromstring(page.html)
        links = []
        for link in dom.xpath(self.xpath):
            links.append(urljoin(url, link))
        return links


class StructureExtractor(ExtractionMapper):

    def __init__(self, length_function, growth_function):
        super(StructureExtractor, self).__init__(
            extraction_function=self._html_to_sequence)
        self.length_function = length_function
        self.growth_function = growth_function

    def _html_to_sequence(self, url, page):
        parser = HTMLSequencer(self.length_function, self.growth_function)
        parser.feed(page.html)
        return parser.get_result()


class GCBlockExtractor(ExtractionMapper):

    def __init__(self):
        super(GCBlockExtractor, self).__init__(
            extraction_function=self._blocks_from_text)
        self.tokenizer = PunktSentenceTokenizer()

    def _blocks_from_text(self, url, page):
        blocks = []
        for sentence in self.tokenizer.sentences_from_text(
                page.text.replace('\n', '')):
            if sentence.strip():
                blocks.append(len(sentence))
            # maybe count tokens? or non-spaces?
        return blocks


class DistanceScorer(object):

    def __init__(self, extraction_mapper, ratio_function, set_based=False):
        self.name = "Default Distance Scorer"
        self.extraction_mapper = extraction_mapper
        self.ratio_function = ratio_function
        self._set_based = set_based
        self._threadsafe = False

    def __str__(self):
        return self.name

    def _score_pair(self, s_idx, s_page, t_idx, t_page):
        """ Overwrite this with you distance of choice """
        return 0

    def _extract(self, source_corpus, target_corpus):
        """ This is called before scoring of pairs.
            Overwrite to extract const data """
        self.sseqs = self.extraction_mapper.extract_source(source_corpus)
        self.tseqs = self.extraction_mapper.extract_target(target_corpus)
        if self._set_based:
            self.sseqs = map(set, self.sseqs)
            self.tseqs = map(set, self.tseqs)

    def score(self, source_corpus, target_corpus, processes=1):
        self._extract(source_corpus, target_corpus)
        sys.stderr.write("Done extracting...\n")
        scoring_matrix = np.zeros((len(source_corpus), len(target_corpus)))
        if processes <= 1:
            for s_idx in xrange(len(self.sseqs)):
                for t_idx in xrange(len(self.tseqs)):
                    scoring_matrix[s_idx, t_idx] = \
                        self.ratio_function(
                            (self.sseqs[s_idx], self.tseqs[t_idx]))
                sys.stderr.write('.')
                sys.stderr.flush()

        else:
            p = multiprocessing.Pool(processes=processes)
            rf = partial(ratio_pool, self.tseqs, self.ratio_function)
            for s_idx, scores in enumerate(
                    p.imap(rf, self.sseqs, chunksize=20)):
                assert len(scores) == len(self.tseqs)
                for t_idx in xrange(len(self.tseqs)):
                    scoring_matrix[s_idx, t_idx] = scores[t_idx]

                if (s_idx + 1) % 20 == 0:
                    sys.stderr.write('.')
                    sys.stderr.flush()
                if (s_idx + 1) % 1000 == 0:
                    sys.stderr.write("[%d]\n" % (s_idx + 1))
            sys.stderr.write("[%d]\n" % len(self.sseqs))
        return scoring_matrix


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


def gc_alignment_score(seq1, seq2):
    gc = GaleChurchWrapper()
    return gc.align_score(seq1, seq2)


class GaleChurchScorer(DistanceScorer):

    def __init__(self):
        super(GaleChurchScorer,
              self).__init__(extraction_mapper=GCBlockExtractor(),
                             ratio_function=gc_alignment_score)


class GaleChurchAlignmentDistance(DistanceScorer):

    def __init__(self):
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


class LinkDistance(DistanceScorer):

    def __init__(self, ratio_function=ratio, xpath='//a/@href'):
        super(LinkDistance, self).__init__(ratio_function=ratio_function)
        self.name = "Link Distance Scorer (xpath: %s)" % xpath
        self.xpath = xpath

    def _extract(self, source_corpus, target_corpus):
        for url, page in source_corpus.iteritems():
            self.sseqs.append(
                self._extract_links(page.url, page.html.encode("utf-8")))
        for url, page in target_corpus.iteritems():
            self.tseqs.append(
                self._extract_links(page.url, page.html.encode("utf-8")))

    def _extract_links(self, url, html):
        dom = lxml.html.fromstring(html)
        links = []
        for link in dom.xpath(self.xpath):
            links.append(urljoin(url, link))
        return links


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


class DictionaryScorer(DistanceScorer):

    def __init__(self, source_tokenizer, target_tokenizer,
                 dictfile, lang1, lang2):
        self.name = "Bitextor-style dictionary scorer"
        self.sdocs = []
        self.tdocs = []
        self.s_words = set()
        self.t_words = set()
        self.read_dictionary(dictfile, lang1, lang2)

        self.source_tokenizer = source_tokenizer
        if not source_tokenizer:
            self.source_tokenizer = SpaceTokenizer()

        self.target_tokenizer = target_tokenizer
        if not target_tokenizer:
            self.target_tokenizer = SpaceTokenizer()

    def read_dictionary(self, filename, lang1, lang2):
        self.dictionary = defaultdict(set)
        swap = False  # switch columns in dict file
        with codecs.open(filename, 'r', 'utf-8', errors='ignore') as dict_file:
            l1, l2 = dict_file.readline().strip().lower().split('\t')
            sys.stderr.write("Translating %s -> %s\n" % (l2, l1))
            if l2 == lang1 and l1 == lang2:
                swap = True
            else:
                assert l1 == lang1 and l2 == lang2, \
                    "unexpected language pair: %s-%s\n" % (l1, l2)

            for line in dict_file:
                if not line.strip():
                    continue
                line = line.strip().lower().split('\t')
                if len(line) != 2:
                    sys.stderr.write("Weird entry: %s\n" % (repr(line)))
                    continue
                w1, w2 = line
                if swap:
                    w1, w2 = w2, w1
                # We're translating lang2 -> lang1 e.g. en -> de
                self.dictionary[w2.strip()].add(w1.strip())
        sys.stderr.write("Read dictionary of %d %s words\n"
                         % (len(self.dictionary), lang2))

    def _extend_dictionary(self, quiet=False):
        n_added = 0
        for w in self.s_words.intersection(self.t_words):
            if w not in self.dictionary[w]:
                n_added += 1
                self.dictionary[w].add(w)
        if not quiet:
            sys.stderr.write("Added %d 1-1 translations\n" % (n_added))
            sys.stderr.write("Final dictionary size: %d\n" %
                             (len(self.dictionary)))

    def _translate_bow(self, bow):
        translation = set()
        n_translated = 0
        for w in bow:
            if w in self.dictionary:
                n_translated += 1
                translation.update(self.dictionary[w])
        return n_translated, translation

    def _words_from_text(self, text, tokenizer):
        words = set()
        for line in text.split("\n"):
            for w in tokenizer.process(line).lower().split():
                words.add(w)
        return words

    def _extract(self, source_corpus, target_corpus):
        for idx, (url, page) in enumerate(source_corpus.iteritems()):
            words = self._words_from_text(page.text, self.source_tokenizer)
            self.s_words.update(words)
            self.sdocs.append(words)

        for idx, (url, page) in enumerate(target_corpus.iteritems()):
            words = self._words_from_text(page.text, self.target_tokenizer)
            self.t_words.update(words)
            self.tdocs.append(words)

        self._extend_dictionary()

    def _bitextor_distance(self, set1, set2):
        # TODO: check if translation is performed in right direction
        n_translated, translated_set2 = self._translate_bow(set2)
        # print set1
        # print set2
        # print n_translated, translated_set2
        # print translated_set2.intersection(set1)
        # sys.exit()
        # size_bigger = max(len(set1), len(set2))
        size_smaller = min(len(set1), len(set2))
        n_common = len(translated_set2.intersection(set1))
        if size_smaller == 0 or n_translated == 0:
            return 0.
        return float(n_common)  # / float(n_translated)
        # return float(size_smaller) / float(size_bigger)
        # return float(size_bigger) / float(size_smaller)
        #     float(n_common) / float(n_translated)

    def _score_pair(self, s_idx, s_page, t_idx, t_page):
        return self._bitextor_distance(self.sdocs[s_idx], self.tdocs[t_idx])


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


class SimhashDistance(DistanceScorer):
    CHAR, TOKEN = range(2)

    def __init__(self, source_tokenizer, target_tokenizer, n=2, level=TOKEN):
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
            # words = page.html.split()
            words = filter(None, re.split("[^0-9a-zA-Z]", page.text))
            return [" ".join(words[i:i + n]) for i in
                    range(max(len(words) - n + 1, 1))]

        def chars(n, tokenizer, page):
            s = "".join(page.text.split())
            return [" ".join(s[i:i + n]) for i in
                    range(max(len(s) - n + 1, 1))]

        def html_tokens(n, tokenizer, page):
            # 153/trigrams
            words = page.html.split()
            return [" ".join(words[i:i + n]) for i in
                    range(max(len(words) - n + 1, 1))]

        if level == SimhashDistance.TOKEN:
            self.source_features = partial(tokens, n, self.source_tokenizer)
            self.target_features = partial(tokens, n, self.target_tokenizer)
        elif level == SimhashDistance.CHARS:
            self.source_features = partial(chars, n, self.source_tokenizer)
            self.target_features = partial(chars, n, self.target_tokenizer)
        # self.source_features = partial(ngrams, n, self.source_tokenizer)
        # self.target_features = partial(ngrams, n, self.target_tokenizer)
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

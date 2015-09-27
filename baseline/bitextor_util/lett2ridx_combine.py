#!/usr/bin/env python

import sys
from operator import itemgetter

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('source', help='source tokens file')
    parser.add_argument('target', help='translated target tokens')
    parser.add_argument('-max_candidates', type=int, default=10,
                        help='maximum number of candidates per document')
    args = parser.parse_args()

    with open(args.source, 'r') as sf:
        for sline in sf:
            s_doc_id, s_tokens = sline.split('\t', 1)
            s_doc_id = int(s_doc_id)
            s_tokens = set(s_tokens.strip().split('\t'))

            similarities = []

            with open(args.target, 'r') as tf:
                for tline in tf:
                    t_doc_id, n_translated, n_orig_tokens, t_tokens = \
                        tline.split('\t', 3)
                    t_doc_id = int(t_doc_id)
                    n_translated = float(n_translated)
                    n_orig_tokens = int(n_orig_tokens)
                    t_tokens = set(t_tokens.strip().split('\t'))

                    # formula from bitextor-idx2ridx
                    max_vocab = float(max(len(s_tokens), n_orig_tokens))
                    min_vocab = float(min(len(s_tokens), n_orig_tokens))
                    num_intersect_words = len(s_tokens.intersection(t_tokens))
                    if max_vocab > 0 and n_translated > 0:
                        similarity = min_vocab / max_vocab * \
                            num_intersect_words / n_translated
                        if s_doc_id == 13 and t_doc_id == 0:
                            print s_tokens
                            print len(s_tokens)
                            print "Original tokens: ", n_orig_tokens
                            print t_tokens
                            print len(t_tokens)

                            # print s_doc_id, t_doc_id
                            print similarity
                            print min_vocab, max_vocab
                            print num_intersect_words,  n_translated
                        similarities.append((t_doc_id, similarity))

            similarities.sort(key=itemgetter(1), reverse=True)
            # High similarity at beginning

            # Fileformat expects docids starting with 1
            sys.stdout.write("%d" % (s_doc_id + 1))
            for t_doc_id, similarity in similarities[:args.max_candidates]:
                sys.stdout.write("\t%d:%f" % (t_doc_id + 1, similarity))
            sys.stdout.write('\n')

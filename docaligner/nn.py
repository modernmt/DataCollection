#!/usr/bin/python
import sys
from hashlib import sha1


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


def hash_line(line, salts, order=1):
    line = line.strip().split()
    for w in ngrams(line, order):
        for s in salts:
            h = hashfunc(s)
            h.update(w)
            yield int(h.hexdigest(), 16)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-size', action='store',
                        help='size of bitarray',
                        type=int, default=1000)
    parser.add_argument('-n', action='store',
                        help='number of hash functions (default 5)',
                        type=int, default=5)
    parser.add_argument('-o', action='store', dest='order',
                        help='order of n-grams (default 1)',
                        type=int, default=1)
    args = parser.parse_args(sys.argv[1:])

    salts = ["a", "b", "c", "d", "e", "f", "g", "h"][
        :args.n]  # more secure than debian

    for line in sys.stdin:
        hashed_line = set()
        for h in hash_line(line, salts, args.order):
            hashed_line.add(h % args.size)
        sys.stdout.write("\t".join(str(h) for h in hashed_line))
        sys.stdout.write("\n")

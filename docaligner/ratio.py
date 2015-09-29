import difflib


def ratio(seq1, seq2):
    s = difflib.SequenceMatcher(None, seq1, seq2)
    return s.ratio()


def quick_ratio(seq1, seq2):
    s = difflib.SequenceMatcher(None, seq1, seq2)
    return s.quick_ratio()


def real_quick_ratio(seq1, seq2):
    s = difflib.SequenceMatcher(None, seq1, seq2)
    return s.real_quick_ratio()


def jaccard(seq1, seq2):
    s1 = set(seq1)
    s2 = set(seq2)
    intersect_size = len(s1.intersection(s2))
    if intersect_size > 0:
        return float(intersect_size) / len(s1.union(s2))
    return 0.

import difflib


def ratio(seq1, seq2):
    s = difflib.SequenceMatcher(None, seq1, seq2)
    return s.ratio()


def ratio_star(seq1_seq2):
    return ratio(*seq1_seq2)


def quick_ratio(seq1, seq2):
    s = difflib.SequenceMatcher(None, seq1, seq2)
    return s.quick_ratio()


def quick_ratio_star(seq1_seq2):
    return quick_ratio(*seq1_seq2)


def real_quick_ratio(seq1, seq2):
    s = difflib.SequenceMatcher(None, seq1, seq2)
    return s.real_quick_ratio()


def real_quick_ratio_star(seq1_seq2):
    return real_quick_ratio(*seq1_seq2)


def jaccard(set1, set2):
    intersect_size = len(set1.intersection(set2))
    if intersect_size > 0:
        return float(intersect_size) / len(set1.union(set2))
    return 0.


def dice(seq1, seq2):
    s1 = set(seq1)
    s2 = set(seq2)
    if len(s1) == 0 and len(s2) == 0:
        return 1.0
    return 2.0 * len(s1.intersection(s2)) / (len(s1) + len(s2))

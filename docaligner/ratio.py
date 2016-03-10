import difflib


def ratio(weights, seq1, seq2):
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


def jaccard(weights, set1, set2):
    intersection = set1.intersection(set2)
    intersect_size = len(intersection)

    # print "Set 1", set1
    # print "Set 2", set2
    # print "Overlap:", intersection
    # print "Weights:"

    if intersect_size > 0:
        return float(intersect_size) / len(set1.union(set2))
        # if weights is None:
        #     return float(intersect_size) / len(set1.union(set2))
        # else:
        #     num = 0.
        #     for term in intersection:
        #         if term in weights:
        # print term, weights[term]
        #             num += weights[term]
        #     denom = 0.
        #     for term in set1.union(set2):
        #         if term in weights:
        #             denom += weights[term]
        #     if denom > 0:
        #         return num / denom
    return 0.


def weighted_jaccard(weights, counts1, counts2):
    num = 0.
    for term, count in (counts1 & counts2).iteritems():
        num += weights[term] * count
    if num > 0:
        denom = 0.
        for term, count in (counts1 | counts2).iteritems():
            denom += weights[term] * count
        return num / denom
    return 0.


def cosine(weights, counts1, counts2):
    nom = 0.
    for term, count in (counts1 & counts2).iteritems():
        nom += counts1[term] * counts2[term] * (weights[term]**2)
    if nom > 0:
        denom = 0.
        for term in counts1:
            denom += (counts1[term] * weights[term])**2
        for term in counts2:
            denom += (counts2[term] * weights[term])**2
        return nom / denom
    return 0.


def dice(seq1, seq2):
    s1 = set(seq1)
    s2 = set(seq2)
    if len(s1) == 0 and len(s2) == 0:
        return 1.0
    return 2.0 * len(s1.intersection(s2)) / (len(s1) + len(s2))

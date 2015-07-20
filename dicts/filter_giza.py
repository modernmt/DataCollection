#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
svocabulary = {}
tvocabulary = {}
svcb = open(sys.argv[1], "r")
tvcb = open(sys.argv[2], "r")
for line in svcb:
    item = line.strip().split(" ")
    svocabulary[item[0]] = item[1]

for line in tvcb:
    item = line.strip().split(" ")
    tvocabulary[item[0]] = item[1]

t3dic = {}
t3s = open(sys.argv[3], "r")
t3t = open(sys.argv[4], "r")
for line in t3t:
    item = line.strip().split(" ")
    if item[1] in t3dic:
        t3dic[item[1]][item[0]] = item[2]
    else:
        t3dic[item[1]] = {}
        t3dic[item[1]][item[0]] = item[2]

for line in t3s:
    item = line.strip().split(" ")
    if item[0] in t3dic:
        if item[1] in t3dic[item[0]]:
            value1 = float(t3dic[item[0]][item[1]])
            value2 = float(item[2])
            hmean = 2 / ((1 / value1) + (1 / value2))
            if hmean > 0.2:
                if item[1] in svocabulary and item[0] in tvocabulary:
                    word1 = svocabulary[item[1]]
                    word2 = tvocabulary[item[0]]
                    print "{0}\t{1}".format(word1, word2)

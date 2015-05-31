#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from collections import defaultdict

magic_number = "df6fa1abb58549287111ba8d776733e9"


langstats = defaultdict(int)

lang = None
for line in sys.stdin:
    if line.startswith(magic_number):
        # df6fa1abb58549287111ba8d776733e9
        # http://www.achpr.org/about/documentation-centre/ language:en
        # offset:200 bytes: 3424
        lang = line.split()[2].split(":")[-1]
        continue
    langstats[lang] += len(line.decode("utf-8").strip())

for lang, num_bytes in langstats.items():
    sys.stdout.write("%s\t%d\n" % (lang, num_bytes))

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

for line in sys.stdin:
    line = line.decode("utf-8").encode("iso-8859-1")  # .decode("utf-8")
    line = line.strip()

    print line.strip()

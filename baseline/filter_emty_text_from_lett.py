#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Removes lines from .lett file where the last column containing base64
encoded text is empty. This otherwise leads to problems downstream. """

import sys

for line in sys.stdin:
    if line.split("\t")[-1].strip():
        sys.stdout.write(line)

#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Converts a bilingual dictionary from Eduard Barbu's format
# to a word-based dictionary usable as a dictionary for Bitextor's
# sentence aligner
#
# Usage: python dict_convert.py < input_dict > output_dict

import sys

# TBD: output language identifiers here; read from command line?
for line in sys.stdin:
    line = line.rstrip('\r\n')
    entry = line.split('@#@')
    source = entry[0].split()
    if len(source) != 1:
	continue
    target = entry[1].split()
    if len(target) != 1:
	continue
    print source[0]+'\t'+target[0]


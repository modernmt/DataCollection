#!/usr/bin/env python
# -*- coding: utf-8 -*-

from urlparse import urlparse
import argparse
import sys

# Takes a sentence-aligned file (typical extension .sent) that includes
# source and target url columns and writes out the corpus separated by domain

parser = argparse.ArgumentParser(description="Output corpus by domain")
parser.add_argument('infile', nargs='?', type=argparse.FileType('r'),
		    default=sys.stdin)
parser.add_argument('-slang', '--lang1', help='source language',
		    dest='source_lang', default='en')
parser.add_argument('-tlang', '--lang2', help='target language',
		    dest='target_lang', default='fr')
args = parser.parse_args()

srcdomain = ""
tgtdomain = ""
for line in args.infile:
    split_line = line.rstrip("\n\r").split("\t")
    if len(split_line) != 4 and len(split_line) !=5:
	sys.exit("Line with inconsistent number of elements")
    source_url, target_url, source, target = split_line[:4]
    srcurl = urlparse(source_url)
    tgturl = urlparse(target_url)
    if srcurl.netloc != tgturl.netloc:
	sys.stderr.write("Domain mismatch {} {}\n".format(source_url,target_url))
	continue
    if srcdomain != srcurl.netloc:
	if srcdomain != "":
	    srcout.close()
	    tgtout.close()
	srcdomain = srcurl.netloc
	tgtdomain = tgturl.netloc
	srcout = open(srcdomain+"."+args.source_lang, "w")
	tgtout = open(tgtdomain+"."+args.target_lang, "w")
    srcout.write(source+"\n")
    tgtout.write(target+"\n")

srcout.close()
tgtout.close()

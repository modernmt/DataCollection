#!/usr/bin/env python
# -*- coding: utf-8 -*-

from urlparse import urlparse
import tldextract
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
parser.add_argument('--regdomain', help='use registered domain without subdomain', action='store_true', default=False)
args = parser.parse_args()

srcdomain = ""
tgtdomain = ""
nwrites = 0
for line in args.infile:
    split_line = line.rstrip("\n\r").split("\t")
    if len(split_line) != 4 and len(split_line) !=5:
	sys.exit("Line with inconsistent number of elements")
    source_url, target_url, source, target = split_line[:4]
    srcurl = urlparse(source_url)
    tgturl = urlparse(target_url)
    if args.regdomain:
	srcext = tldextract.extract("http://"+srcurl.netloc)
	tgtext = tldextract.extract("http://"+tgturl.netloc)
	new_srcdomain = srcext.registered_domain
	new_tgtdomain = tgtext.registered_domain
    else:
	new_srcdomain = srcurl.netloc
	new_tgtdomain = tgturl.netloc
    if new_srcdomain != new_tgtdomain:
	sys.stderr.write("Domain mismatch {} {}\n".format(source_url,target_url))
	continue
    if srcdomain != new_srcdomain:
	if srcdomain != "":
	    srcout.close()
	    tgtout.close()
	srcdomain = new_srcdomain
	tgtdomain = new_tgtdomain
	srcout = open(srcdomain+"."+args.source_lang, "a")
	tgtout = open(tgtdomain+"."+args.target_lang, "a")
    srcout.write(source+"\n")
    tgtout.write(target+"\n")
    nwrites += 1

print "Number of lines written: {}".format(nwrites)
srcout.close()
tgtout.close()

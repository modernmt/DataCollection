#!/usr/bin/python

import sys
import re

if len(sys.argv) != 2:
    print "Usage: python "+sys.argv[0]+" language_id"
    exit()

langid = sys.argv[1]

r = re.compile("(\S*"+langid+"\S*?)\t(.*?)\t")
for line in sys.stdin:
    m = r.match(line)
    if m:
	(urlsource, urltarget) = m.group(1,2)
	print urlsource+"\t"+urltarget


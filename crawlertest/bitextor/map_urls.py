#!/usr/bin/python

import sys
import glob

if len(sys.argv) != 2:
    print "Usage: python "+sys.argv[0]+" mapping_dir"
    exit()

# Read mapping files into dictionary
mappings = sys.argv[1]
mapping = {}
for mapfile in glob.iglob(mappings+"/*.mapping"):
    f = open(mapfile)
    for line in f:
	(filename,url) = line.split()
	mapping[filename] = url

for line in sys.stdin:
    (filesource, filetarget) = line.split()
    if filesource in mapping:
	if filetarget in mapping:
	    print mapping[filesource]+"\t"+mapping[filetarget]
	else:
	    sys.stderr.write("Target file mapping not found:"+filetarget+"\n")
    else:
	sys.stderr.write("Source file mapping not found:"+filesource+"\n")


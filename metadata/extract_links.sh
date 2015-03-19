#!/bin/bash

# Downloads $1 which should be a CommonCrawl wat file,
# extracts links, sorts by domainname and xzips the result

FILENAME=`echo $1 | awk  ' BEGIN { FS = "/" } { print $(NF) }'`
OUTFILE=${FILENAME/warc.wat.gz/links.xz}

# Directory in which this script is stored
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

curl -s $1 | gzip -cd | ${DIR}/links_from_wat.py | sort -t" " -k1,1 | xz > ${OUTFILE}
#!/bin/bash

# Downloads $1 which should be a CommonCrawl wat file,
# extracts links, sorts by domainname and xzips the result

# Exit as soon as any command fails
set -e

FILENAME=`echo $1 | awk  ' BEGIN { FS = "/" } { print $(NF-2) "/" $(NF) }'`
OUTFILE=${FILENAME/warc.wat.gz/links.xz}
TMPDIR=./tmp/`hostname`
mkdir -p ${TMPDIR}

# Directory in which this script is stored
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

curl -s --retry 5 $1 | gzip -cd | ${DIR}/links_from_wat.py | sort -t" " -S500M -k1,1 --compress-program=pigz --temporary-directory=${TMPDIR} --parallel=2 | uniq | /home/buck/net/build/pxz/pxz -T 2 -9 -e > ${OUTFILE} && touch ${OUTFILE/links.xz/done}

#!/bin/bash

set -e
set -o pipefail

FILENAME=$(echo $1 | awk ' BEGIN { FS = "/" } { print $(NF-2) "/" $(NF)}')

if [ ! -f ${FILENAME}.done ]; then
  curl -s $1 | gzip -cd | \
  /fs/nas/heithrun0/commoncrawl/langsplit/bin/read_wet.py | \
  /fs/nas/heithrun0/commoncrawl/langsplit/bin/langsplit --printchunks 2> /dev/null | \
  xz -9 -e > ${FILENAME}.langsplit.xz
  touch ${FILENAME}.done
fi

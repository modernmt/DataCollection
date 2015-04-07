#!/bin/bash

# Downloads $1 which should be a CommonCrawl wat file,
# extracts links, sorts by domainname and xzips the result

# Exit as soon as any command fails
set -e
set -o pipefail

# Directory in which this script is stored
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )

PREFIX=$(dirname ${1}/x | awk -F '/' '{print $NF}')

zcat ${1}/*.links.gz | \
pypy ${DIR}/add_warc_locations.py --prefix=${PREFIX}/ <(zcat /fs/gna0/buck/cc/warc2stats/baseline_candidates.gz) | \
gzip -9 > ${1}/baseline_locations.gz
touch ${1}/baseline_locations.done

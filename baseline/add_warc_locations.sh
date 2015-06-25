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
python ${DIR}/add_warc_locations.py --prefix=${PREFIX}/ /home/achim/stats/found_urls.txt \
> ${1}/found_locations.txt
touch ${1}/found_locations.done

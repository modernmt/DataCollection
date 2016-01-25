#!/bin/bash

# Downloads pages given location in S3, extracts text, calls bitextors
# hunalign wrapper and filters the resulting bitext.

# Exit as soon as any command fails
set -e
set -o pipefail

source /home/buck/net/build/virtualenvs/crawl/bin/activate

BASEDIR=$1
PREFIX=$2

SLANG=en
TLANG=it

# Directory in which this script is stored
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
MOSESDIR=/home/buck/net/build/moses-clean/
BITEXTORDIR=/home/buck/net/build/bitextor/

# Step 1: Download page pairs from S3
DONEFILE=${BASEDIR}/locations/${PREFIX}.done
if [ ! -f ${DONEFILE} ]; then
  echo "Downloading locations from ${BASEDIR}/locations/${PREFIX}.loc.gz"
  zcat ${BASEDIR}/locations/${PREFIX}.loc.gz | \
  nice parallel -j 32 --pipe -L 2 \
    ${DIR}/candidates2corpus.py \
        -source_splitter="'${MOSESDIR}/scripts/ems/support/split-sentences.perl -l ${SLANG} -b -q'" \
        -target_splitter="'${MOSESDIR}/scripts/ems/support/split-sentences.perl -l ${TLANG} -b -q'" | \
  nice pigz -9 > ${BASEDIR}/downloaded/${PREFIX}.down.gz
  zcat ${BASEDIR}/downloaded/${PREFIX}.down.gz | wc -l
  touch ${DONEFILE}
fi

# Step 2: Use bitextors wrapper around hunalign
DONEFILE=${BASEDIR}/downloaded/${PREFIX}.done
if [ ! -f ${DONEFILE} ]; then
  zcat ${BASEDIR}/downloaded/${PREFIX}.down.gz |
  nice parallel --pipe ${BITEXTORDIR}/bin/bitextor-align-segments \
    --lang1 ${SLANG} --lang2 ${TLANG} \
    -d ${BITEXTORDIR}/dictionaries-hunalign/${SLANG}-${TLANG}.dic | \
  nice pigz -9 > ${BASEDIR}/aligned/${PREFIX}.aligned.gz
  zcat ${BASEDIR}/aligned/${PREFIX}.aligned.gz | wc -l
  touch ${DONEFILE}
fi

# Step 3: Filter bad sentence pairs
DONEFILE=${BASEDIR}/aligned/${PREFIX}.done
if [ ! -f ${DONEFILE} ]; then
  zcat ${BASEDIR}/aligned/${PREFIX}.aligned.gz |
  cut -f 3- | \
  ${DIR}/filter_hunalign_bitext.py - ${BASEDIR}/filtered/${PREFIX}.filtered \
    -s ${SLANG} -t ${TLANG} \
  > ${BASEDIR}/filtered/${PREFIX}.deleted
  wc -l ${BASEDIR}/filtered/${PREFIX}.*
  pigz -9 ${BASEDIR}/filtered/${PREFIX}.*
  touch ${DONEFILE}
fi

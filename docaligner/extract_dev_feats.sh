#!/usr/bin/env bash

# Exit as soon as any command fails
set -e
set -o pipefail

source /home/buck/net/build/virtualenvs/crawl/bin/activate


BASENAME=${1/.lett/}
F=${BASENAME}.feats
LOG=${BASENAME}.log
TARGETS=${BASENAME}.targets
TEXT_EN=${BASENAME}.text.en
TEXT_DE=${BASENAME}.text.de

SLANG=en
TLANG=fr

BINDIR=/home/buck/net/build/DataCollection

# ${BINDIR}/baseline/extract_foreign_text.py -splitter='' -normalizer='' -tokenizer='' -o ${TEXT_DE} -lang de < $1 &
# ${BINDIR}/baseline/extract_foreign_text.py -splitter='' -normalizer='' -tokenizer='' -o ${TEXT_EN} -lang en < $1 &


# exit

${BINDIR}/docaligner/extract_features.py $1 BOW -tlang=${TLANG} -out $F.bow_n1_jaccard -source_tokenizer="/home/buck/net/build/moses-clean/scripts/tokenizer/tokenizer.perl -b -l ${SLANG}" -target_tokenizer="/home/buck/net/build/moses-clean/scripts/tokenizer/tokenizer.perl -b -l ${TLANG}" -targets ${TARGETS} -n 1 &>${LOG}

${BINDIR}/docaligner/extract_features.py $1 BOW -tlang=${TLANG} -out $F.bow_n2_jaccard -source_tokenizer="/home/buck/net/build/moses-clean/scripts/tokenizer/tokenizer.perl -b -l ${SLANG}" -target_tokenizer="/home/buck/net/build/moses-clean/scripts/tokenizer/tokenizer.perl -b -l ${TLANG}" -n 2 &>>${LOG}

${BINDIR}/docaligner/extract_features.py $1 BOW -tlang=${TLANG} -out $F.bow_n3_jaccard -source_tokenizer="/home/buck/net/build/moses-clean/scripts/tokenizer/tokenizer.perl -b -l ${SLANG}" -target_tokenizer="/home/buck/net/build/moses-clean/scripts/tokenizer/tokenizer.perl -b -l ${TLANG}" -n 3 &>>${LOG}

${BINDIR}/docaligner/extract_features.py $1 Simhash -tlang=${TLANG} -out $F.simhash_n2 -source_tokenizer="/home/buck/net/build/moses-clean/scripts/tokenizer/tokenizer.perl -b -l ${SLANG}" -target_tokenizer="/home/buck/net/build/moses-clean/scripts/tokenizer/tokenizer.perl -b -l ${TLANG}" -n 2 &>>${LOG}

${BINDIR}/docaligner/extract_features.py $1 Simhash -tlang=${TLANG} -out $F.simhash_n3 -source_tokenizer="/home/buck/net/build/moses-clean/scripts/tokenizer/tokenizer.perl -b -l ${SLANG}" -target_tokenizer="/home/buck/net/build/moses-clean/scripts/tokenizer/tokenizer.perl -b -l ${TLANG}" -n 3 &>>${LOG}

${BINDIR}/docaligner/extract_features.py $1 LinkDistance -tlang=${TLANG} -out $F.linkdistance_a -source_tokenizer="/home/buck/net/build/moses-clean/scripts/tokenizer/tokenizer.perl -b -l ${SLANG}" -target_tokenizer="/home/buck/net/build/moses-clean/scripts/tokenizer/tokenizer.perl -b -l ${TLANG}" &>>${LOG}

${BINDIR}/docaligner/extract_features.py $1 LinkDistance -tlang=${TLANG} -out $F.linkdistance_img -source_tokenizer="/home/buck/net/build/moses-clean/scripts/tokenizer/tokenizer.perl -b -l ${SLANG}" -target_tokenizer="/home/buck/net/build/moses-clean/scripts/tokenizer/tokenizer.perl -b -l ${TLANG}" -xpath="//img/@src" &>>${LOG}

${BINDIR}/docaligner/extract_features.py $1 TranslatedBOW -tlang=${TLANG} -out $F.tbow -source_tokenizer="/home/buck/net/build/moses-clean/scripts/tokenizer/tokenizer.perl -b -l ${SLANG}" -target_tokenizer="/home/buck/net/build/moses-clean/scripts/tokenizer/tokenizer.perl -b -l ${TLANG}" -dictfile /home/buck/net/build/bitextor/baseline/en-fr.dic &>>${LOG}

${BINDIR}/docaligner/extract_features.py $1 Structure -tlang=${TLANG} -out $F.structure -source_tokenizer="/home/buck/net/build/moses-clean/scripts/tokenizer/tokenizer.perl -b -l ${SLANG}" -target_tokenizer="/home/buck/net/build/moses-clean/scripts/tokenizer/tokenizer.perl -b -l ${TLANG}" -n 2 &>>${LOG}

wait

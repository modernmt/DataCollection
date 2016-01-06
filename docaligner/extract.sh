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

BINDIR=/home/buck/net/build/DataCollection

# ${BINDIR}/baseline/extract_foreign_text.py -splitter='' -normalizer='' -tokenizer='' -o ${TEXT_DE} -lang de < $1 &
# ${BINDIR}/baseline/extract_foreign_text.py -splitter='' -normalizer='' -tokenizer='' -o ${TEXT_EN} -lang en < $1 &


# exit

${BINDIR}/docaligner/extract_features.py $1 BOW -tlang=de -out $F.bow_n1_jaccard -source_tokenizer="/home/buck/net/build/moses-clean/scripts/tokenizer/tokenizer.perl -b -l en" -target_tokenizer="/home/buck/net/build/moses-clean/scripts/tokenizer/tokenizer.perl -b -l de" -n 1 -targets ${TARGETS} &>${LOG}

${BINDIR}/docaligner/extract_features.py $1 BOW -tlang=de -out $F.bow_n2_jaccard -source_tokenizer="/home/buck/net/build/moses-clean/scripts/tokenizer/tokenizer.perl -b -l en" -target_tokenizer="/home/buck/net/build/moses-clean/scripts/tokenizer/tokenizer.perl -b -l de" -n 2 &>>${LOG}

${BINDIR}/docaligner/extract_features.py $1 BOW -tlang=de -out $F.bow_n3_jaccard -source_tokenizer="/home/buck/net/build/moses-clean/scripts/tokenizer/tokenizer.perl -b -l en" -target_tokenizer="/home/buck/net/build/moses-clean/scripts/tokenizer/tokenizer.perl -b -l de" -n 3 &>>${LOG}

${BINDIR}/docaligner/extract_features.py $1 Structure -tlang=de -out $F.structure -source_tokenizer="/home/buck/net/build/moses-clean/scripts/tokenizer/tokenizer.perl -b -l en" -target_tokenizer="/home/buck/net/build/moses-clean/scripts/tokenizer/tokenizer.perl -b -l de" -n 2 &>>${LOG}

${BINDIR}/docaligner/extract_features.py $1 Simhash -tlang=de -out $F.simhash_n2 -source_tokenizer="/home/buck/net/build/moses-clean/scripts/tokenizer/tokenizer.perl -b -l en" -target_tokenizer="/home/buck/net/build/moses-clean/scripts/tokenizer/tokenizer.perl -b -l de" -n 2 &>>${LOG}

${BINDIR}/docaligner/extract_features.py $1 Simhash -tlang=de -out $F.simhash_n3 -source_tokenizer="/home/buck/net/build/moses-clean/scripts/tokenizer/tokenizer.perl -b -l en" -target_tokenizer="/home/buck/net/build/moses-clean/scripts/tokenizer/tokenizer.perl -b -l de" -n 3 &>>${LOG}

${BINDIR}/docaligner/extract_features.py $1 LinkDistance -tlang=de -out $F.linkdistance_a -source_tokenizer="/home/buck/net/build/moses-clean/scripts/tokenizer/tokenizer.perl -b -l en" -target_tokenizer="/home/buck/net/build/moses-clean/scripts/tokenizer/tokenizer.perl -b -l de" &>>${LOG}

${BINDIR}/docaligner/extract_features.py $1 LinkDistance -tlang=de -out $F.linkdistance_img -source_tokenizer="/home/buck/net/build/moses-clean/scripts/tokenizer/tokenizer.perl -b -l en" -target_tokenizer="/home/buck/net/build/moses-clean/scripts/tokenizer/tokenizer.perl -b -l de" -xpath="//img/@src" &>>${LOG}

${BINDIR}/docaligner/extract_features.py $1 TranslatedBOW -tlang=de -out $F.tbow -source_tokenizer="/home/buck/net/build/moses-clean/scripts/tokenizer/tokenizer.perl -b -l en" -target_tokenizer="/home/buck/net/build/moses-clean/scripts/tokenizer/tokenizer.perl -b -l de" -dictfile /home/buck/net/build/bitextor/bitextor-code/dicts/de/en-de.dic &>>${LOG}


wait

#!/bin/bash

set -e -o pipefail

DICT=$1
LETT=$2

LETTR=${LETT}r
IDX=${LETT/lett/idx}
RIDX=${LETT/lett/ridx}
DIST=${LETT/lett/dist}
DOCS=${LETT/lett/docs}
SENT=${LETT/lett/sent}
LOG=${LETT/lett/log}

BT=/home/buck/net/build/bitextor/bin

mv ${LETT} ${LETT}.bak
/home/buck/net/build/DataCollection/baseline/filter_emty_text_from_lett.py < ${LETT}.bak > ${LETT}
echo -n "LETT .. LETTR .. "
${BT}/bitextor-lett2lettr < ${LETT} > ${LETTR}
echo -n "IDX .. "
python ${BT}/bitextor-lett2idx < ${LETTR} > ${IDX}
echo -n "RIDX .. "
python ${BT}/bitextor-idx2ridx < ${IDX} -d ${DICT} --lang1 en --lang2 fr > ${RIDX}
echo -n "DIST .. "
${BT}/bitextor-distancefilter -l ${LETTR} ${RIDX}  > ${DIST}
echo -n "DOCS .. "
${BT}/bitextor-align-documents ${RIDX} -l ${LETTR}  > ${DOCS}
echo -n "SENTS .. "
${BT}/bitextor-align-segments --lang1 en --lang2 fr -d ${DICT} < ${DOCS} > ${SENT} 2> ${LOG}
echo -n "Cleaning up .. "
rm -f ${IDX} ${LETTR} ${RIDX} ${DIST} ${DOCS} ${LOG}
rm ${LETT}
mv ${LETT}.bak ${LETT}
echo "Done! "
echo -n "EN: " 
cut -f 3 ${SENT} | wc
echo -n "FR: " 
cut -f 4 ${SENT} | wc

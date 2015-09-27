#!/bin/bash

# Exit as soon as any command fails
set -e
set -o pipefail

DICT=$1
LETT=$2

LETTR=${LETT}r
IDX=${LETT/lett/idx}
RIDXS=${LETT/lett/ridx_s}
RIDXT=${LETT/lett/ridx_t}
RIDX=${LETT/lett/ridx}
DIST=${LETT/lett/dist}
DOCS=${LETT/lett/docs}
SENT=${LETT/lett/sent}

BT=/home/buck/net/build/bitextor/bin

DONEFILE=${LETT/.lett/.done}
LOG=${LETT/.lett/.log}

if [ ! -f ${DONEFILE} ]; then
    source /home/buck/net/build/virtualenvs/crawl/bin/activate
    # Need to have the punk tokenizer from nltk
    #echo -e "import nltk\nnltk.download('punkt')" | python 2> /dev/null

    ls -lh ${LETT}
    date  >> ${LOG}
    echo "LETT .. LETTR .. " >> ${LOG}
    cat ${LETT} | /home/buck/net/build/DataCollection/baseline/filter_emty_text_from_lett.py | python ${BT}/bitextor-lett2lettr > ${LETTR}
    
    echo "RIDX .. " >> ${LOG}
    /home/buck/net/build/DataCollection/baseline/bitextor_util/lett2ridx_map.py ${LETTR}  -lang1 en -lang2 fr > ${RIDXS} 2>> ${LOG}
    /home/buck/net/build/DataCollection/baseline/bitextor_util/lett2ridx_map.py ${LETTR}  -lang1 en -lang2 fr -dict ${DICT} > ${RIDXT} 2>> ${LOG}
    /home/buck/net/build/DataCollection/baseline/bitextor_util/lett2ridx_combine.py ${RIDXS} ${RIDXT} > ${RIDX}
    #python ${BT}/bitextor-lett2idx --lang1 en --lang2 fr < ${LETTR} > ${IDX}
    #echo "RIDX .. " >> ${LOG}
    #python ${BT}/bitextor-idx2ridx < ${IDX} -d ${DICT} --lang1 en --lang2 fr > ${RIDX}
    echo "DIST .. " >> ${LOG}
    python ${BT}/bitextor-distancefilter -l ${LETTR} ${RIDX}  > ${DIST}
    echo "DOCS .. " >> ${LOG}
    python  ${BT}/bitextor-align-documents ${RIDX} -l ${LETTR}  > ${DOCS}
    echo "SENTS .. " >> ${LOG}
    python  ${BT}/bitextor-align-segments --lang1 en --lang2 fr -d ${DICT} < ${DOCS} > ${SENT} 2>> ${LOG}
    echo "Cleaning up .. " >> ${LOG}
    rm -f ${IDX} ${LETTR} ${RIDX} ${DIST} ${DOCS} ${RIDXS} ${RIDXT}
    echo "Done! " >> ${LOG}
    echo -n "EN: " >> ${LOG}
    cut -f 3 ${SENT} | wc >> ${LOG}
    echo -n "FR: " >> ${LOG}
    cut -f 4 ${SENT} | wc >> ${LOG}

    date  >> ${LOG}
    touch ${DONEFILE}
fi

#!/bin/bash

# Exit as soon as any command fails
set -e
set -o pipefail

# default values
BT=/home/buck/net/build/bitextor/bin
DC=/home/buck/net/build/DataCollection
LANG2=fr
MAXOCC=15
LOWMEM=0

ARGS=$(getopt -o i:d:m:t:b:c: -l "lett:,dict:,maxocc:,targetlang:,bitextor:,datacollection:,lowmem" -n "getopt.sh" -- "$@");

#Bad arguments
if [ $? -ne 0 ];
then
  echo "Bad arguments"
  exit 1
fi

eval set -- "$ARGS";

while true; do
  case "$1" in
    -i|--lett)
      shift;
      if [ -n "$1" ]; then
        LETT=$1
        shift;
      fi
      ;;
    -d|--dict)
      shift;
      if [ -n "$1" ]; then
        DICT=$1
        shift;
      fi
      ;;
    -m|--maxocc)
      shift;
      if [ -n "$1" ]; then
        MAXOCC=$1
        shift;
      fi
      ;;
    -t|--targetlang)
      shift;
      if [ -n "$1" ]; then
        LANG2=$1
        shift;
      fi
      ;;
    -b|--bitextor)
      shift;
      if [ -n "$1" ]; then
        BT=$1
        shift;
      fi
      ;;
    --datacollection)
      shift;
      if [ -n "$1" ]; then
        DC=$1
        shift;
      fi
      ;;
    --lowmem)
      shift;
      LOWMEM=1
      ;;
    --)
      shift;
      break;
      ;;
  esac
done

if [ ! -f ${LETT} ]; then
  echo "Cannot find lett file: " $LETT
  exit
fi

if [ ! -f ${DICT} ]; then
  echo "Cannot find dictionary: " $DICT
  exit
fi


LETTR=${LETT}r
IDX=${LETT/lett/idx}
RIDX=${LETT/lett/ridx}
WCOUNTS=${LETT/lett/wcounts}
RIDXS=${LETT/lett/ridx_s}
RIDXT=${LETT/lett/ridx_t}
DIST=${LETT/lett/dist}
DOCS=${LETT/lett/docs}
SENT=${LETT/lett/sent}
CLEAN=${LETT/lett/clean}


DONEFILE=${LETT/.lett/.done}
LOG=${LETT/.lett/.log}

if [ ! -f ${DONEFILE} ]; then
    export BITEXTORBIN=${BT}
    #source /home/buck/net/build/virtualenvs/crawl/bin/activate
    # Need to have the punk tokenizer from nltk
    echo -e "import nltk\nnltk.download('punkt')" | python 2> /dev/null

    ls -lh ${LETT}
    echo "Starting at" `date` > ${LOG}
    echo "LETT .. LETTR .. " >> ${LOG}
    ${DC}/baseline/filter_emty_text_from_lett.py < ${LETT} | python ${BT}/bitextor-lett2lettr > ${LETTR}

    if [ $LOWMEM -eq 0 ]; then    
        echo "IDX .. " >> ${LOG}
        python ${BT}/bitextor-lett2idx -m ${MAXOCC} --lang1 en --lang2 ${LANG2} < ${LETTR} > ${IDX}
        echo "RIDX .. " >> ${LOG}
        python ${BT}/bitextor-idx2ridx < ${IDX} -d ${DICT} --lang1 en --lang2 ${LANG2} > ${RIDX}
    else
        echo "LOWMEM RIDX .. " >> ${LOG}
        ${DC}/baseline/bitextor_util/wordcounts.py ${LETT} -lang1 en -lang2 ${LANG2} -m ${MAXOCC} -once > ${WCOUNTS} 
        ${DC}/baseline/bitextor_util/lett2ridx_map.py ${LETT} ${WCOUNTS} -lang1 en -lang2 ${LANG2} > ${RIDXS} 2>> ${LOG}
        ${DC}/baseline/bitextor_util/lett2ridx_map.py ${LETT} ${WCOUNTS} -lang1 en -lang2 ${LANG2} -dict ${DICT} > ${RIDXT} 2>> ${LOG}
        ${DC}/baseline/bitextor_util/lett2ridx_combine.py ${RIDXS} ${RIDXT} > ${RIDX}
    fi

    python ${BT}/bitextor-distancefilter -l ${LETTR} ${RIDX}  > ${DIST}
    echo "DOCS .. " >> ${LOG}
    python  ${BT}/bitextor-align-documents ${DIST} -l ${LETTR} > ${DOCS}
    echo "SENTS .. " >> ${LOG}

    HUNALIGN_DICT=$(mktemp /tmp/hunalign_dic.XXXXXX)
    tail -n +2 ${DICT} | sed -r 's/^([^\s]+)\t([^\s]+)$/\2 @ \1/g' > $HUNALIGN_DICT

    python  ${BT}/bitextor-align-segments --lang1 en --lang2 ${LANG2} -d ${HUNALIGN_DICT} < ${DOCS} > ${SENT} 2>> ${LOG}
    echo "CLEAN_ALIGN .. " >> ${LOG}
    python ${BT}/bitextor-cleantextalign -q 0 -m 5 < ${SENT} > ${CLEAN} 2>>${LOG}
    echo "Cleaning up .. " >> ${LOG}
    rm -f ${IDX} ${LETTR} ${RIDX} ${DIST} ${DOCS} ${RIDXS} ${RIDXT} ${WCOUNTS} ${SENT} ${IDX} translate.txt 
    echo "Done! " >> ${LOG}
    echo -n "SOURCE: " >> ${LOG}
    cut -f 3 ${CLEAN} | wc >> ${LOG}
    echo -n "TARGET: " >> ${LOG}
    cut -f 4 ${CLEAN} | wc >> ${LOG}

    echo "Done at: " date  >> ${LOG}
    touch ${DONEFILE}
fi

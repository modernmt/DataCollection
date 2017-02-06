#! /bin/bash

lng=$1; shift

if [ ! -d monolingual/${lng}  ] ; then mkdir -p monolingual/${lng} ; fi

pushd monolingual/${lng}

case $lng in
  en)
    version_UEDIN=deduped_en
    iterlist1="0 1 2 3 4"
    iterlist2="0"
    
    wget http://data.statmt.org/ngrams/deduped/meta/wc.txt
    for i1 in $iterlist1 ; do
    for i2 in $iterlist2 ; do
        if [ ! -e ${lng}.${i1}${i2}.xz ] ; then        
            wget http://data.statmt.org/ngrams/deduped_en/${lng}.${i1}${i2}.xz
            cat wc.txt | grep ${lng}.${i1}${i2} > ${lng}.${i1}${i2}.wc
        fi
    done
    done
    cat ${lng}.*.wc | awk '{totLines+=$1; totWords+=$2; totChars+=$3;} END { print totLines,totWords,totChars; }' > ${lng}.wc
    ;;
  *)
    echo "for languages different from ${lng} (English) please use the script scripts/get_monolingual_corpus.sh" ; exit 1
    ;;
esac

popd


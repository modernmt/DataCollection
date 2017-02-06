#!/bin/bash
lng=$1; shift

dir=monolingual
maxWords=2000000000

scriptDir=$(cd $(dirname $0) ; pwd)

case $lng in
  en)
    ;;
  *)
    echo unknown lng $lng ; exit 1
    ;;
esac


function get_seeded_random()
{
  seed="$1"
  openssl enc -aes-256-ctr -pass pass:"$seed" -nosalt \
    </dev/zero 2>/dev/null
}

function reduce_by_size (){
local lng=$2
local lines=$3
local words=$4
local maxWords=$5
local index=$6

name=tmp$$_${lng}

reducedLines=$(( $lines * $maxWords / $words ))
echo "keep only $reducedLines (= $lines * $maxWords / $words ) sentences randomly chosen from the corpus, because it is too large"
#perform several (100) repetitions of the extraction, because of the limited RAM of the machine)
repetitions=100
repLines=$(( $lines / $repetitions ))
reducedLines=$(( $reducedLines / $repetitions ))
date
xzcat ${lng}.${index}.xz | split --verbose -d -a 3 -l $repLines - ${name}_part
rep=0
for part in ${name}_part* ; do 
seed=$(( 1234 + $rep ))
date
echo "shuffling rep=$rep seed=$seed index=$index tailLines=$tailLines headLines=$headLines reducedLines=$reducedLines"
cat $part | shuf --head-count $reducedLines --random-source=<(get_seeded_random $seed)  >> selected.${index}.${lng}
rep=$(( $rep + 1 ))
rm $part 
done
date
}


#figures for lines and words corresponds to the 'wc -lw' counts reported in the ${lng}.wc
#downloaded together with the .xz files (see script "get_monolingual_corpus_English.sh")

iterlist1="0 1 2 3 4"
iterlist2="0"
    
if [ -d ${dir}/${lng} ] ; then
    if [ -n "$(ls -A ${dir}/${lng}/selected.${lng} 2> /dev/null)" ] ; then
        echo "${dir}/${lng}/selected.${lng}   already exists; please remove before proceeding"
        exit 1
    fi
else
        echo "${dir}/${lng}   does not exist; please run get_monolingual_corpus_English.sh before"
        exit 1
fi
    

pushd ${dir}/${lng}

for i1 in $iterlist1 ; do
for i2 in $iterlist2 ; do
    if [ -n "$(ls -A selected.${index}.${lng} 2> /dev/null)" ] ; then
        echo "selected.${index}.${lng}   already exists; please remove before proceeding"
        exit 1
    fi
done
done

for i1 in $iterlist1 ; do
for i2 in $iterlist2 ; do


    lines=`cat ${lng}.${i1}${i2}.wc | awk '{print $1}'`
    words=`cat ${lng}.${i1}${i2}.wc | awk '{print $2}'`
    
    index=${i1}${i2}

    reduce_by_size ${lng} ${lines} ${words} ${maxWords} ${index}
    date

    cat selected.${index}.${lng} | ${scriptDir}/prepro_en/scripts/split-sentences.perl -l ${lng} -splitlinebreak > selected_split.${index}.${lng} 
    date

    wc selected.${index}.${lng} selected_split.${index}.${lng}

    cat selected.${index}.${lng} >> selected.${lng}
    rm selected.${index}.${lng} 
    date

    cat selected_split.${index}.${lng} >> selected_split.${lng}
    rm selected_split.${index}.${lng}
    date
   
    
done
done

wc selected.${lng} > selected.${lng}.wc 
wc selected_split.${lng} > selected_split.${lng}.wc

popd

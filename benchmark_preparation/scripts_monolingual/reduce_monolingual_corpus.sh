#!/bin/bash
lng=$1; shift

dir=monolingual
maxWords=2000000000

scriptDir=$(cd $(dirname $0) ; pwd)


case $lng in
  en)
    echo "for ${lng} (English) please use the script scripts/reduce_monolingual_corpora_English.sh" ; exit 1
    ;;
  de|es|fr|it|ru)
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
local lng=$1
local lines=$2
local words=$3
local maxWords=$4

name=tmp$$_${lng}

reducedLines=$(( $lines * $maxWords / $words ))
echo "keep only $reducedLines (= $lines * $maxWords / $words ) sentences randomly chosen from the corpus, because it is too large"
#perform several (100) repetitions of the extraction, because of the limited RAM of the machine)
repetitions=100
repLines=$(( $lines / $repetitions ))
reducedLines=$(( $reducedLines / $repetitions ))
date
xzcat ${lng}.xz | split --verbose -d -a 3 -l $repLines - ${name}_part
rep=0
for part in ${name}_part* ; do 
seed=$(( 1234 + $rep ))
date
echo "shuffling rep=$rep seed=$seed reducedLines=$reducedLines"
cat $part | shuf --head-count $reducedLines --random-source=<(get_seeded_random $seed)  >> selected.${lng}
rep=$(( $rep + 1 ))
rm $part 
done
date

}


#figures for lines and words corresponds to the 'wc -lw' counts reported in the $i{lng}.wc
#downloaded together with the .xz files (see script "get_monolingual_corpus.sh")
#for "it" the figures are actually recomputed, because the original file is corrupted; 

if [ -d ${dir}/${lng} ] ; then
    if [ -n "$(ls -A ${dir}/${lng}/selected.${lng} 2> /dev/null)" ] ; then
        echo "${dir}/${lng}/selected.${lng}   already exists; please remove before proceeding"
        exit 1
    fi
else
        echo "${dir}/${lng}   does not exist; please run get_monolingual_corpus.sh before"
        exit 1
fi


pushd ${dir}/${lng}


lines=`cat ${lng}.wc | awk '{print $1}'`
words=`cat ${lng}.wc | awk '{print $2}'`

reduce_by_size ${lng} ${lines} ${words} ${maxWords}
date

cat selected.${lng} | ${scriptDir}/prepro_en/scripts/split-sentences.perl -l ${lng} -splitlinebreak > selected_split.${lng} 
date

wc selected.${lng} > selected.${lng}.wc 
wc selected_split.${lng} > selected_split.${lng}.wc
date

popd


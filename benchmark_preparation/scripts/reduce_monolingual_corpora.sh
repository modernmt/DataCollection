#!/bin/bash
lng=$1; shift

function get_seeded_random()
{
  seed="$1"
  openssl enc -aes-256-ctr -pass pass:"$seed" -nosalt \
    </dev/zero 2>/dev/null
}

function reduce_by_size (){
local dir=$1
local lng=$2
local lines=$3
local words=$4
local maxWords=$5
if [ -d ${dir}/${lng} ] ; then
date
pushd ${dir}/${lng}

name=tmp$$_${lng}
xzcat ${lng}.xz > ${name}

if [ -n "$(ls -A ${dir}/${lng}/selected.${lng} 2> /dev/null)" ] ; then
echo "${dir}/${lng}/selected.${lng}   already exists; please remove before proceeding"
else

reducedLines=$(( $lines * $maxWords / $words ))
echo "keep only $reducedLines (= $lines * $maxWords / $words ) sentences randomly chosen from the corpus, because it is too large"
#perform several (100) repetitions of the extraction, because of the limited RAM of the machine)
repetitions=100
repLines=$(( $lines / $repetitions ))
reducedLines=$(( $reducedLines / $repetitions ))
date
split --verbose -d -a 3 -l $repLines $name ${name}_part
rep=0
for part in ${name}_part* ; do 
seed=$(( 1234 + $rep ))
date
echo "shuffling rep=$rep seed=$seed tailLines=$tailLines headLines=$headLines reducedLines=$reducedLines"
cat $part | shuf --head-count $reducedLines --random-source=<(get_seeded_random $seed)  >> selected.${lng}
rep=$(( $rep + 1 ))
done
date
rm ${name}_part* 
date
rm $name
date
fi
popd
fi

}

case $lng in
  en)
    echo "for ${lng} (English) please use the script scripts/reduce_monolingual_corpora_English.sh" ; exit 1
    ;;
  de|es|fr|it)
    ;;
  *)
    echo unknown lng $lng ; exit 1
    ;;
esac


dir=monolingual
maxWords=2000000000

#figures for lines and words corresponds to the 'wc -lw' counts reported in the $i{lng}.wc
#downloaded together with the .xz files (see script "get_monolingual_corpus.sh")
#for "it" the figures are actually recomputed, because the original file is corrupted; 
#for "en" the figures are the sum of the used subfiles (see script "get_monolingual_corpus.sh")

lines=`cat ${lng}.wc | awk '{print $1}'`
words=`cat ${lng}.wc | awk '{print $2}'`

reduce_by_size ${dir} ${lng} ${lines} ${words} ${maxWords}
date

cat selected.${lng} | scripts/prepro_en/scripts/split-sentences.perl -l ${lng} -splitlinebreak > selected_split.${lng} 
date

wc selected.${lng} selected_split.${lng}
date


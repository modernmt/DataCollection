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
local index=$6
if [ -d ${dir}/${lng} ] ; then
date
pushd ${dir}/${lng}

name=tmp$$_${lng}.${index}
case $lng in
  en)
    xzcat ${lng}.${indes}.xz > ${name}
    ;;
  *)
    echo unknown lng $lng ; exit 1
    ;;
esac

if [ -n "$(ls -A ${dir}/${lng}/selected.${index}.${lng} 2> /dev/null)" ] ; then
echo "${dir}/${lng}/selected.${index}.${lng}   already exists; please remove before proceeding"
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
echo "shuffling rep=$rep seed=$seed index=$index tailLines=$tailLines headLines=$headLines reducedLines=$reducedLines"
cat $part | shuf --head-count $reducedLines --random-source=<(get_seeded_random $seed)  >> selected.${index}.${lng}
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

dir=monolingual
maxWords=2000000000

#figures for lines and words corresponds to the 'wc -lw' counts reported in the $i{lng}.wc
#downloaded together with the .xz files (see script "get_monolingual_corpus.sh")
#for "it" the figures are actually recomputed, because the original file is corrupted; 
#for "en" the figures are the sum of the used subfiles (see script "get_monolingual_corpus.sh")

lines=`cat ${lng}.wc | awk '{print $1}'`
words=`cat ${lng}.wc | awk '{print $2}'`

iterlist1="0 1 2 3 4"
iterlist2="0"
    
for i1 in $iterlist1 ; do
for i2 in $iterlist2 ; do
    lines=`cat ${lng}.${i1}${i2}.wc | awk '{print $1}'`
    words=`cat ${lng}.${i1}${i2}.wc | awk '{print $2}'`
    
    index=${i1}${i2}

    reduce_by_size ${dir} ${lng} ${lines} ${words} ${maxWords} ${index}
    date

    cat selected.${index}.${lng} | scripts/prepro_en/scripts/split-sentences.perl -l ${lng} -splitlinebreak > selected_split.${index}.${lng} 
    date

    wc selected.${index}.${lng} selected_split.${index}.${lng}
    date

done
done

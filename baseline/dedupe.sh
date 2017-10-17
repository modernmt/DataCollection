#!/bin/bash

# Usage: dedupe.sh <input folder> <output folder> <sourcelangid> <targetlangid>

# Location of dedupe binary built from https://github.com/kpu/preprocess
dedupebin=~/preprocess/bin/dedupe

if [ ! -d $1 ]
then
    echo "$1 is not a folder."
    exit
fi

if [ -e $2]
then
    if [ ! -d $2 ]
    then
	echo "$2 is not a directory."
	exit
    fi
else
    mkdir -p $2
fi

for insrc in $1/*.$3
do
    intgt=${insrc%.$3}.$4
    outsrc=$2/${insrc##*/}
    outtgt=$2/${intgt##*/}
    `$dedupebin $insrc $intgt $outsrc $outtgt`
done


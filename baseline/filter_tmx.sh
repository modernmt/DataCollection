#!/bin/bash

SLOC=$1
shift
TLOC=$1
shift

# Extract language identifiers and TMX base name
SLANG=${SLOC%%-*}
TLANG=${TLOC%%-*}
echo $SLOC
echo $TLOC
echo $SLANG
echo $TLANG
for TMX in $@
do
    FILENAME=$(basename $TMX) 
    BASE=${FILENAME%.*}

    echo $TMX
    echo $BASE

    # Conversion with tmx2txt.pl (specific language identifier needed)

    echo "$TMX to bitext conversion ..."
    perl ~/m4loc/tmx/tmx2txt.pl $SLOC $TLOC $BASE $TMX
     
    # Pasteing together into one tab-delimited file

    echo "Pasteing into one tab-delimited file ..."
    paste $BASE.$SLOC $BASE.$TLOC > $BASE

    # Cleaning with filter_hunalign_bitext.py

    echo "Cleaning the bitext ..." 
    python ~/DataCollection/baseline/filter_hunalign_bitext.py -deleted ${BASE}.deleted -slang $SLANG -tlang $TLANG -cld2 $BASE ${BASE}.filtered

    # Separation with cut into two language files (name _langid.bitext)

    echo "Separation into two language files ..." 
    cut -f1 ${BASE}.filtered > ${BASE}_${SLANG}
    cut -f2 ${BASE}.filtered > ${BASE}_${TLANG}

    # tar two files into one .tar

    echo "Packaging with tar ..."
    tar -cvf ${BASE}_filtered.tar ${BASE}_${SLANG} ${BASE}_${TLANG}

    # Gzip

    echo "Compression with gzip ..."
    gzip ${BASE}_filtered.tar

done


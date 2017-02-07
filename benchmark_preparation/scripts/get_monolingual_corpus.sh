#! /bin/bash

lng=$1; shift

if [ ! -d monolingual/${lng}  ] ; then mkdir -p monolingual/${lng} ; fi

pushd monolingual/${lng}

case $lng in
  de|es|fr|ru)
    wget http://data.statmt.org/ngrams/deduped/meta/${lng}.wc
    if [ ! -e ${lng}.xz ] ; then
        wget http://data.statmt.org/ngrams/deduped/${lng}.xz
    fi
    ;;
  it)
    if [ ! -e it.deduped.xz ] ; then
        wget http://data.statmt.org/ngrams/deduped/${lng}.deduped.xz
        mv ${lng}.deduped.xz ${lng}.xz
        ln -s ${lng}.xz ${lng}.deduped.xz
        xzcat ${lng}.xz | wc > ${lng}.wc
    fi
    ;;
  en)
    echo "for ${lng} (English) please use the script scripts/get_monolingual_corpus_Englsh.sh" ; exit 1
    ;;
  *)
    echo unknown lng $lng ; exit 1
    ;;
esac

popd


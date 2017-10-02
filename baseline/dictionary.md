## Building bilingual dictionaries for additional translation directions

To support sentence alignment with the hunalign tool bilingual word dictionaries are needed in Step 5 of the [baseline process](/baseline/baseline.md). These can be built from existing parallel corpora.

### Prerequisites
* An Ubuntu/Debian-based operating system
* An installation of the [Moses MT toolkit](http://www.statmt.org/moses/) 
* An installation of [MGIZA](https://github.com/moses-smt/mgiza)
The following instructions assume installation in your home directory.

## Dictionary build process
The parallel corpus to build the dictionary from should consist of about over 100,000 sentence pairs and be available as two text files named `Corpus.sourcelanguageid` and `Corpus.targetlanguageid`.
```bash
~/moses/scripts/tokenizer/tokenizer.perl -l sourcelanguageid < Corpus.sourcelanguageid > Corpus.tok.sourcelanguageid
~/moses/scripts/tokenizer/tokenizer.perl -l targetlanguageid < Corpus.targetlanguageid > Corpus.tok.targetlanguageid
~/moses/scripts/tokenizer/lowercase.perl < Corpus.tok.sourcelanguageid > Corpus.lower.sourcelanguageid
~/moses/scripts/tokenizer/lowercase.perl < Corpus.tok.targetlanguageid > Corpus.lower.targetlanguageid

~/mgiza/mgizapp/bin/mkcls -pCorpus.lower.sourcelanguageid -VCorpus.lower.sourcelanguageid.vcb.classes
~/mgiza/mgizapp/bin/mkcls -pCorpus.lower.targetlanguageid -VCorpus.lower.targetlanguageid.vcb.classes

~/mgiza/mgizapp/bin/plain2snt Corpus.lower.sourcelanguageid Corpus.lower.targetlanguageid

nohup ~/mgiza/mgizapp/bin/snt2cooc Corpus.lower.targetlanguageid_Corpus.lower.sourcelanguageid.cooc Corpus.lower.targetlanguageid.vcb Corpus.lower.sourcelanguageid.vcb Corpus.lower.targetlanguageid_Corpus.lower.sourcelanguageid.snt &

mkdir Corpus
mkdir Corpus2

nohup ~/mgiza/mgizapp/bin/mgiza -S Corpus.lower.targetlanguageid.vcb -T Corpus.lower.sourcelanguageid.vcb -C Corpus.lower.targetlanguageid_Corpus.lower.sourcelanguageid.snt -o DC -outputpath Corpus -coocurrencefile Corpus.lower.targetlanguageid_Corpus.lower.sourcelanguageid.cooc &

nohup ~/mgiza/mgizapp/bin/snt2cooc Corpus.lower.sourcelanguageid_Corpus.lower.targetlanguageid.cooc Corpus.lower.sourcelanguageid.vcb Corpus.lower.targetlanguageid.vcb Corpus.lower.sourcelanguageid_Corpus.lower.targetlanguageid.snt &

nohup ~/mgiza/mgizapp/bin/mgiza -S Corpus.lower.sourcelanguageid.vcb -T Corpus.lower.targetlanguageid.vcb -C Corpus.lower.sourcelanguageid_Corpus.lower.targetlanguageid.snt -o DC -outputpath Corpus2 -coocurrencefile Corpus.lower.sourcelanguageid_Corpus.lower.targetlanguageid.cooc &

python ~/DataCollection/dicts/filter_giza.py Corpus.lower.sourcelanguageid.vcb Corpus.lower.targetlanguageid.vcb ./Corpus/DC.t3.final ./Corpus2/DC.t3.final > sourcelanguageid_targetlanguageid.dict.unsorted
cat sourcelanguageid_targetlanguageid.dict.unsorted | sort > sourcelanguageid_targetlanguageid.dict.sorted
```
Add a header line `sourcelanguageid<tab>targetlanguageid` to the resulting `sourcelanguageid_targetlanguageid.dict.sorted` to produce the final dictionary.

## Creating dictionaries for reverse language directions

To create a dictionary for a reverse language from a dictionary in Bitextor format (described in Step 5 of the [baseline documentation](/baseline/baseline.md)):
* Remove first line with language identifiers and save the result as `en-de.nohead.dic`
* Reverse the order of the dictionary entries and sort the results with the command `awk '{print $2 " " $1}' en-de.nohead.dic | sort > de-en.dic`
* Add a header line `de<tab>en` to the reversed `de-en.dic`

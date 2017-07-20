# Dictionaries for sentence alignment with Bitextor

## Dictionary purpose
Running [sentence alignment](https://github.com/ModernMT/DataCollection/blob/dev/baseline/baseline.md#step-5-run-bitextorhunalign-to-extract-parallel-sentences) 
requires a word-based bilingual dictionary in the format required by [Bitextor](https://sourceforge.net/projects/bitextor/):
* First line: `<source language identifier><tab><target language identifier>`
* Remaining lines: `<source word><tab><target word>`

Alternatively the `<tab>` can be replaced with a `<space>`.

Some dictionaries are available in Bitextor and some in the `dicts` folder in this repository.

## Dictionary building from a parallel corpus
The word-based bilingual dictionary for Bitextor does not need to be especially clean, so an automated process by word aligning a parallel corpus can be used. It is still important that the dictionary contains most generic vocabulary for a language, so choosing a generic parallel corpus to build the dictionary from is preferable.

The following instructions use the multi-threaded word alignment tool [mgiza](https://github.com/moses-smt/mgiza). The instructions assume that this tool is installed.

### Tokenizing and lowercasing the parallel corpus
After obtaining a suitable parallel corpus it will have to be tokenized and lowercased in preparation for the word alignment:
```
~/moses/scripts/tokenizer/tokenizer.perl -l <source language id> < Corpus.<source language id> > Corpus.tok.<source language id>
~/moses/scripts/tokenizer/tokenizer.perl -l <target language id> < Corpus.<target language id> > Corpus.tok.<target language id>
~/moses/scripts/tokenizer/lowercase.perl < Corpus.tok.<source language id> > Corpus.lower.<source language id>
~/moses/scripts/tokenizer/lowercase.perl < Corpus.tok.<target language id> > Corpus.lower.<target language id>
```

### Building vocabulary, sentence and cooccurrence files 
In preparation for word alignment vocabulary, sentence and cooccurrence files need to be built:
```
~/mgiza/mgizapp/bin/mkcls -pCorpus.lower.<source language id> -VCorpus.lower.<source language id>.vcb.classes
~/mgiza/mgizapp/bin/mkcls -pCorpus.lower.<target language id> -VCorpus.lower.<target language id>.vcb.classes

~/mgiza/mgizapp/bin/plain2snt Corpus.lower.<source language id> Corpus.lower.<target language id>

~/mgiza/mgizapp/bin/snt2cooc Corpus.lower.<target language id>_Corpus.lower.<source language id>.cooc Corpus.lower.<target language id>.vcb Corpus.lower.<source language id>.vcb Corpus.lower.<target language id>_Corpus.lower.<source language id>.snt
~/mgiza/mgizapp/bin/snt2cooc Corpus.lower.<source language id>_Corpus.lower.<target language id>.cooc Corpus.lower.<source language id>.vcb Corpus.lower.<target language id>.vcb Corpus.lower.<source language id>_Corpus.lower.<target language id>.snt
```

### Word alignment with mgiza
Word alignments are done both in the forward and backward language direction:
```
mkdir Corpus
mkdir Corpus2

nohup ~/mgiza/mgizapp/bin/mgiza -S Corpus.lower.<target language id>.vcb -T Corpus.lower.<source language id>.vcb -C Corpus.lower.<target language id>_Corpus.lower.<source language id>.snt -o DC -outputpath Corpus -coocurrencefile Corpus.lower.<target language id>_Corpus.lower.<source language id>.cooc &
nohup ~/mgiza/mgizapp/bin/mgiza -S Corpus.lower.<source language id>.vcb -T Corpus.lower.<target language id>.vcb -C Corpus.lower.<source language id>_Corpus.lower.<target language id>.snt -o DC -outputpath Corpus2 -coocurrencefile Corpus.lower.<source language id>_Corpus.lower.<target language id>.cooc &
```

### Combining the word alignment information into a single dictionary
As a last step the word alignment information is combined into a single dictionary using the script `filter_giza.py` contained in this repository and sorted:
```
python ~/DataCollection/dicts/filter_giza.py Corpus.lower.<source language id>.vcb Corpus.lower.<target language id>.vcb ./Corpus/DC.t3.final ./Corpus2/DC.t3.final > <source language id>-<target language id>.dict.unsorted

cat <source language id>-<target language id>.dict.unsorted | sort > <source language id>-<target language id>.dic
```

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
### Tokenizing and lowercasing the parallel corpus
After obtaining a suitable parallel corpus it will have to be tokenized and lowercased in preparation for the word alignment:


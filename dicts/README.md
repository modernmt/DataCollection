# Dictionaries for sentence alignment with Bitextor

## Dictionary purpose
Running [sentence alignment](https://github.com/ModernMT/DataCollection/blob/dev/baseline/baseline.md#step-5-run-bitextorhunalign-to-extract-parallel-sentences) 
requires a word-based bilingual dictionary in the format required by [Bitextor](https://sourceforge.net/projects/bitextor/):
* First line: `<source language identifier><tab><target language identifier>`
* Remaining lines: `<source word><tab><target word>`

Alternatively the `<tab>` can be replaced with a `<space>`.

Some dictionaries are available in Bitextor and some in the `dicts` folder in this repository.

## Dictionary creation from a parallel corpus

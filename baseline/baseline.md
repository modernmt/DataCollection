# Running a baseline
This document describes how to generate a parallel corpus from a [CommonCrawl](http://commoncrawl.org/) crawl. It requires that language meta-data has been extracted from the crawl via the process described in `metadata\metadata.md` and is accessible through a meta-data server. Another requirement is that the software described in `install.md` has been installed. *Baseline* in this context means that a simple URL matching mechanism is applied along with standard sentence alignment provided by the Bitextor/hunalign tools.

## Step 1: Preparations

### Creating a folder for the baseline results
```
cd
mkdir -p experiments/baseline/en_de_2015_32
cd experiments/baseline/en_de_2015_32
```
In this case a parallel English-German corpus should be extracted from the 2015_32 (July 2015) CommonCrawl. The crawl identifiers can be found here http://commoncrawl.org/the-data/get-started/.

## Step 2: Produce candidate urls
One result of the meta-data processing is a *_kv* file that contains the CommonCrawl URLs tagged with languages identified for the page content with a language identifier. KV files for some of the CommonCrawls can be found at http://www.statmt.org/~buck/mmt/langstat_kv/

### Extracting candidate URLs for the target language
```
nohup gzip -cd /mnt/langsplit/2015_32_kv.gz | /usr/bin/parallel -j 4 --block=100M --pipe ~/DataCollection/baseline/langstat2candidates.py -lang de > candidates_de 2> candidates_target.log &
```
The use of [GNU Parallel](http://www.gnu.org/software/parallel/) is optional, but speeds things up - here with the use of four processor cores in parallel. It doesn't make sense to run `parallel` with more jobs than processor cores (`-j 4`), you can also set `-j 0` that uses as many as possible (see GNU Parallel documentation http://www.gnu.org/software/parallel/man.html).

### Sorting the target language URL candidates
```
nohup sort -u -k 1,1 --compress-program=pigz candidates_de > candidates.de 2> candidates_target_sort.log &
```
### Matching the target language URLs with source language URLs
```
nohup gzip -cd /mnt/langsplit/2015_32_kv.gz | /usr/bin/parallel -j 4 --block=100M --pipe ~/DataCollection/baseline/langstat2candidates.py -lang=en -candidates candidates.de | sort -u -k 1,1 --compress-program=pigz > candidates.en-de 2> match.log &
```

If you are collecting data for a language direction for which you already earlier collected data from the reverse direction, please see an optimized process in the appendix.

## Step 3: Look up where these URLs appear in CommonCrawl S3
```
nohup cat candidates.en-de | nice ~/DataCollection/baseline/locate_candidates.py - - -server='http://statmt.org:8084/query_prefix' > candidates.en-de.locations 2> locate.log &
```

## Step 4: Download pages from CommonCrawl S3 and extract text
```
nohup cat candidates.en-de.locations | ~/DataCollection/baseline/candidates2corpus.py -source_splitter='/moses_install_location/scripts/ems/support/split-sentences.perl -l en -b -q' -target_splitter='/moses_install_location/scripts/ems/support/split-sentences.perl -l de -b -q' > en-de.down 2> candidates2corpus.log &
```
This step uses the language-specific sentence splitter contained in the Moses MT system. See the installation instructions in `INSTALL.md` for details.

## Step 5: Run Bitextor/Hunalign to extract parallel sentences

```
nohup pv en-de.down | parallel --pipe /usr/local/bin/bitextor-align-segments --lang1 en --lang2 de -d ~/DataCollection/dicts/en-de.dic > en-de.sent 2> align.log &
```
When using `cat` instead of `pv` the machine might run out of memory.

Running the sentence alignment requires a word-based bilingual dictionary in the format required by Bitextor:
* First line: `<source language identifier><tab><target language identifier>`
* Remaining lines: `<source word><tab><target word>`

Some dictionaries are available in Bitextor and some in the `dicts` folder in this repository.

The resulting `en-de.sent` file has 5 columns: source URL, target URL, source text, target text, and hunalign score. The columns can be extracted into individual files using the `cut` command, e.g. `cut -f 3 en-de.sent` to extract the source text.

## Step 6: Clean parallel sentences
This step is optional, but applies some common-sense cleaning filters to the extracted bitext.

```
nohup cat en-de.sent | ~/DataCollection/baseline/filter_hunalign_bitext.py - en-de.filtered --lang1 en --lang2 de -cld2 -deleted en-de.deleted 2> filter.log &
```
This needs cld2-cffi and langid so run `pip install langid cld2-cffi` first. The resulting file has 3 columns: source text, target text, and hunalign score. As above use `cut` to get source/target.

## Step 7: Extracting the text by web domain
If the extraction by pairs of corpus files by web domain is desired rather than large parallel corpus files, the following commands can be used:

```
mkdir webdomain_registered
cd webdomain_registered
nohup python ~/DataCollection/baseline/corpus_by_domain.py -slang en -tlang de --regdomain ../en-de.filtered 2> ../webdomain_registered_err.log &
```
The option `--regdomain` extracts the files by registered domain (i.e. without subdomains). The parameter can be omitted to extract by subdomain.


## Appendix

### Generating candidate URL pairs for reverse language directions (optional optimization)
Because of the way that URL candidate extraction works, the extraction for a reverse language direction - in our example German-Italian - would generate a lot of duplicate candidates (in some of our experiments around 90%). Because we do not have a way to detect the translation direction (i.e. what was the original text and what the translation), this generates a lot of duplicate work. Thus the corpus from the original language direction (in our case English-German) can just be reversed. In order to collect data only for pages that were not contained in the original language direction, this process can be used:

```
awk '{print $1 " " $4 " " $3 " " $2 " " $5}' /location_original_language_direction/candidates.en-de > candidates.de-en.exclude
sort candidates.de-en candidates.de-en.exclude candidates.de-en.exclude | uniq -u > candidates.de-en.unique
```

Then use the file `candidates.de-en.unique` as input for Step 3.

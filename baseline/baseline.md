# Running a baseline
This document describes how to generate a parallel corpus from a [CommonCrawl](http://commoncrawl.org/) crawl. It requires that language meta-data has been extracted from the crawl via the process described in `metadata\metadata.md` and is accessible through a meta-data server. Another requirement is that the software described in `install.md` has been installed. *Baseline* in this context means that a simple URL matching mechanism is applied along with standard sentence alignment provided by the Bitextor/hunalign tools.

For the easiest start we also provide already matched URL files annotated with CommonCrawl locations for a selection of language pairs that can be used to start in Step 4. of this baseline process. The files are contained in compressed form in our releases on https://github.com/ModernMT/DataCollection/releases

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
Particularly if the target language is English, this command might run out of memory. For the typical CommonCrawl size this can be fixed by increasing RAM to 32 GB and omit parallelization:
```
nohup gzip -cd /mnt/langsplit/2015_32_kv.gz | ~/DataCollection/baseline/langstat2candidates.py -lang=en -candidates candidates.de | sort -u -k 1,1 --compress-program=pigz > candidates.en-de 2> match.log &
```

In case candidates were already crawled earlier for a reverse language direction or an earlier CommonCrawl you might want to remove any duplicates to avoid duplication in the resulting corpus. See the [appendix](/baseline/baseline.md#appendix) for instructions how to generate a deduplicated candidate list. 

## Step 3: Look up where these URLs appear in CommonCrawl S3

### Option 1 (use the [CommonCrawl Index API](http://commoncrawl.org/2015/04/announcing-the-common-crawl-index/))
```
nohup cat candidates.en-de | nice ~/DataCollection/baseline/locate_candidates_cc_index_api.py - - > candidates.en-de.locations 2> locate.log &
```
The script uses the index server provided by CommonCrawl, which is often overloaded/slow to respond. To speed up the process, you can run your own index server (recommended in the AWS us-east region to be close to the data the server accesses). When running your own index server edit the variable `COMMONCRAWL_INDEX_URL` in `locate_candidates_cc_index_api.py` to point to your index server.

### Option 2 (if you have built your own location database - *deprecated*)
*This option is deprecated - see more details in the [meta-data generation documentation](/metadata/metadata.md).*

```
nohup cat candidates.en-de | nice ~/DataCollection/baseline/locate_candidates.py - - -server='http://statmt.org:8084/query_prefix' > candidates.en-de.locations 2> locate.log &
```



## Step 4: Download pages from CommonCrawl S3 and extract text
For certain language pairs we provide the `.locations` files in compressed form in our releases on https://github.com/ModernMT/DataCollection/releases. You can use these files to start the process in this step.
```
nohup cat candidates.en-de.locations | ~/DataCollection/baseline/candidates2corpus.py -source_splitter='/moses_install_location/scripts/ems/support/split-sentences.perl -l en -b -q' -target_splitter='/moses_install_location/scripts/ems/support/split-sentences.perl -l de -b -q' > en-de.down 2> candidates2corpus.log &
```
This step uses the language-specific sentence splitter contained in the Moses MT system. See the installation instructions in `INSTALL.md` for details.

## Step 5: Run Bitextor/Hunalign to extract parallel sentences

```
nohup cat en-de.down | parallel --pipe /usr/local/bin/bitextor-align-segments --lang1 en --lang2 de -d ~/DataCollection/dicts/en-de.dic > en-de.sent 2> align.log &
```
(If the machine runs out of memory in this step try `pv` instead of `cat`.)

Running the sentence alignment requires a word-based bilingual dictionary in the format required by Bitextor:
* First line: `<source language identifier><tab><target language identifier>`
* Remaining lines: `<source word><tab><target word>`

Some dictionaries are available in Bitextor and some in the `dicts` folder in this repository. Additional instructions are available how to create a dictionaries for [new translation directions](/baseline/dictionary.md) and [reverse translation directions](/baseline/dictionary.md#creating-dictionaries-for-reverse-language-directions) from existing dictionaries.

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

### Generating candidate URL pairs for reverse language directions
Because of the way that URL candidate extraction works, the extraction for a reverse language direction - in our example German-English - would generate a lot of duplicate candidates (in some of our experiments around 90%). Because we do not have a way to detect the translation direction (i.e. what was the original text and what the translation), this generates a lot of duplicate work. Thus the corpus from the original language direction (in our case English-German) can just be reversed. In order to collect data only for pages that were not contained in the original language direction, this process can be used:

```
awk '{print $1 " " $4 " " $3 " " $2 " " $5}' /location_original_language_direction/candidates.en-de > candidates.de-en.exclude
sort candidates.de-en candidates.de-en.exclude candidates.de-en.exclude | uniq -u > candidates.de-en.unique
```

Then use the file `candidates.de-en.unique` as input for Step 3.

### Deduplicating URL pairs across different CommonCrawls

Because CommonCrawl crawls have a varying [degree of overlap between crawls](https://commoncrawl.github.io/cc-crawl-statistics/plots/crawloverlap) it is a good idea to deduplicate candidates generated in step 2. for the same language pair with candidates from earlier crawls to avoid duplicate data from the same pages. Keep in mind that pages change over time and new bilingual content could have been added. 

To exclude pages that were already crawled for the English-German direction from CommonCrawl 2015_27 (assuming that we did this earlier), follow this process:

```
sed 's/2015_27/2015_32/g' candidates.en-de.2015_27 > candidates.en-de.exclude_from_2015_32
sort candidates.en-de candidates.en-de.exclude_from_2015_32 candidates.en-de.exclude_from_2015_32 | uniq -u > candidates.en-de.unique
```

Then use the file `candidates.de-en.unique` as input for Step 3.

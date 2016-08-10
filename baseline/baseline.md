# Running a baseline
```
cd
mkdir -p experiments/baseline/en-de
cd experiments/baseline/en-de
```

## Step 1: Produce candidate urls
```
curl http://www.statmt.org/~buck/mmt/langstat_kv/2015_27_kv.gz | gzip -cd | head -n 10000000 | nice python /home/buck/net/build/DataCollection/baseline/langstat2candidates.py -lang=de | sort -u -k 1,1 --compress-program=pigz > candidates.de
curl http://www.statmt.org/~buck/mmt/langstat_kv/2015_27_kv.gz | gzip -cd | head -n 10000000 | nice python /home/buck/net/build/DataCollection/baseline/langstat2candidates.py -lang=en -candidates candidates.de | sort -u -k 1,1 --compress-program=pigz > candidates.en-de
```
The `head` command should be removed when wanting to produce all candidate URLs from a crawl.

### Alternative: Run with gnu parallel to speed things up. Replace 'python' with 'parallel --block=200M --pipe -j 4 python'
```
curl http://www.statmt.org/~buck/mmt/langstat_kv/2015_27_kv.gz | gzip -cd | head -n 10000000 | nice parallel --block=200M --pipe -j 4 python /home/buck/net/build/DataCollection/baseline/langstat2candidates.py -lang=de | sort -u -k 1,1 --compress-program=pigz > candidates.de
curl http://www.statmt.org/~buck/mmt/langstat_kv/2015_27_kv.gz | gzip -cd | head -n 10000000 | nice parallel --block=200M --pipe -j 4 python /home/buck/net/build/DataCollection/baseline/langstat2candidates.py -lang=en -candidates candidates.de | sort -u -k 1,1 --compress-program=pigz > candidates.en-de
```
It probably doesn't make sense to run `parallel` with more jobs than processor cores (`-j 4`), you can also set `-j 0` that uses as many as possible (see GNU Parallel documentation http://www.gnu.org/software/parallel/man.html).

## Step 2: Look up where these URLs appear in S3
```
cat candidates.en-de | nice /home/buck/net/build/DataCollection/baseline/locate_candidates.py - - -server='http://statmt.org:8084/query_prefix' > candidates.en-de.locations
```

## Step 3: Download pages from S3 and extract text
```
cat candidates.en-de.locations | /home/buck/net/build/DataCollection/baseline/candidates2corpus.py -source_splitter='/home/buck/net/build/mosesdecoder/scripts/ems/support/split-sentences.perl -l en -b -q' -target_splitter='/home/buck/net/build/mosesdecoder/scripts/ems/support/split-sentences.perl -l de -b -q'  > en-de.down
```

## Step 4: Run Hunalign to extract parallel sentences

```
pv en-de.down | parallel --pipe /usr/local/bin/bitextor-align-segments --lang1 en --lang2 de -d de-en.dic > en-de.sent
```
When using `cat` instead of `pv` the machine might run out of memory.

The resulting `en-de.sent` file has 5 columns: source URL, target URL, source text, target text, and hunalign score. The columns can be extracted into individual files using the `cut` command, e.g. `cut -f 3 en-de.sent` to extract the source text.

## Step 5: Clean parallel sentences

```
cut -f 3- en-de.sent | /home/buck/net/build/DataCollection/baseline/filter_hunalign_bitext.py - en-de.filtered --lang1 en --lang2 de -cld2 -deleted del
```
This needs cld2-cffi and langid so run `pip install langid cld2-cffi` first. The resulting file has 3 columns: source text, target text, and hunalign score. As above use `cut` to get source/target.

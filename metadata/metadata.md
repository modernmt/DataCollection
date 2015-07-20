## Intro

For each page in CommonCrawl we hold as metadata

* The location of the raw download in S3. This is given as a URL plus offset and length.
* The languages discovered by CLD2 in the raw text of the page. This is given as a list of (Language / Number of bytes) pairs.

## Getting location data
For recent crawls we use the data files from the common crawl index. These are just 300 gzipped files containing key-value pairs.

```
for i in `seq -w 0 299`; do wget -c https://aws-publicdatasets.s3.amazonaws.com/common-crawl/cc-index/collections/CC-MAIN-2015-22/indexes/cdx-00${i}.gz; done
```

## Building data database from location data

  for f in /fs/nas/eikthyrnir0/commoncrawl/cdx/2015_22/cdx-00???.gz; do echo `date` $f ; zcat $f | nice python ~/net/build/DataCollection/metadata/metadatabase.py --cdx 2015_22 cdx --db db_2015_22 --batchsize 100000; done


## Getting the language distribution data

Language distribution in computed by feeding raw text dumps (the .wet files) into CLD2.

Example for May 2015 crawl:

```
# Get filelist
mkdir 2015_22
cd 2015_22
wget https://aws-publicdatasets.s3.amazonaws.com/common-crawl/crawl-data/CC-MAIN-2015-22/wet.paths.gz

# Convert to HTTPS URLs
zcat wet.paths.gz | sed 's/^/https:\/\/aws-publicdatasets.s3.amazonaws.com\//' > $wet.paths.http

# Make subdirectories
for f in `zcat wet.paths.gz |  cut -d '/' -f 5 | sort | uniq`; do mkdir -p $f; done; 

# Collect monolingual data
# Set number of jobs to roughly half the number of cores, e.g. -j8 on a 16-core machine.
cat wet.paths.http | \
parallel --nice 19 --progress --sshloginfile -j 12 --wd `pwd` /path/to/DataCollection/metadata/extract_monolingual.sh
```

This will take a few days even on a multicore machine. Re-run the last line to make sure all files are properly processed. Finished files will not be processed again.

## Updating entries in the metadatabase with the new language statistics.

Compile the updatekv executeable in DataCollection/metadata/leveldb.

```
xzcat 2015_22/*.internal.warc.wet.gz.langsplit.xz | \
/path/to/DataCollection/metadata/langstats2kv.py 2015_22 | \
/path/to/DataCollection/metadata/leveldb db_2015_22

```

## Metadata API

The metadata API allows querying with a partial URL prefix and (optionally) a crawl name. Subdomains are ignored.

    $ curl "http://statmt.org:9231/query_domain?domain=hettahuskies&crawl=2013_20"

    {
      "unique_urls": [
        "http://hettahuskies.com/farm&dogs/AboutHuskies/famous.php",
        "http://hettahuskies.com/",
        "http://hettahuskies.com/landpgru.php",
        "http://hettahuskies.com/Location/When2come/w2cintro.php",
        "http://hettahuskies.com/activities/MultiActivity/MAWAW.php",
        "http://hettahuskies.com/activities/SingleDay/SDlss.php",
        "http://hettahuskies.com/activities/MultiActivity/MASAD.php",
        "http://hettahuskies.com/Location/Location&maps/Scandinavia.php",
        "http://www.hettahuskies.com/",
        "http://www.hettahuskies.com/landpgfr.php",
        "http://hettahuskies.com/activities/FarmVisits/FVintro.php",
        "http://www.hettahuskies.com/landpggr.php",
        "http://hettahuskies.com/activities/MultiDay/MDintro.php",
        "http://hettahuskies.com/Location/Areaattractions/aaintro.php"
      ],
      "query_domain": "hettahuskies",
      "query_path": "",
      "query_crawl": "2013_20"
    }

Note how subdomains are (intentionally) ignored. If there were other suffixes but .com they would all be here. Include the suffix if needed:

    $ curl "http://statmt.org:9231/query_domain?domain=hettahuskies.de&crawl=2013_20"

    {
      "unique_urls": [],
      "query_domain": "hettahuskies",
      "query_path": "",
      "query_crawl": "2013_20"
    }

No results here because we only have .com urls for that domain. 

If 'crawl' is not specified, we get results from all crawls at once. For now only 2013_20 is indexed though. Get a list by using the _crawls_ endpoint:

    $ curl "http://statmt.org:9231/crawls"
    {
      "crawls": [ "2013_20" ]
    }

You can also query a full prefix of the path:

    $ curl "http://statmt.org:9231/query_domain?domain=hettahuskies.com/Loc"

    {
      "unique_urls": [
        "http://hettahuskies.com/Location/Location&maps/Scandinavia.php",
        "http://hettahuskies.com/Location/When2come/w2cintro.php",
        "http://hettahuskies.com/Location/Areaattractions/aaintro.php"
      ],
      "query_domain": "hettahuskies",
      "query_path": "/Loc",
      "query_crawl": ""
    }

To get the full metadata stored for each URL just add &full:

    curl "http://statmt.org:9231/query_domain?domain=hettahuskies.com/Loc&full"
    {
      "unique_urls": [
        "http://hettahuskies.com/Location/Location&maps/Scandinavia.php", 
        "http://hettahuskies.com/Location/When2come/w2cintro.php", 
        "http://hettahuskies.com/Location/Areaattractions/aaintro.php"
      ], 
      "query_domain": "hettahuskies", 
      "query_path": "/Loc", 
      "data": {
        "http://hettahuskies.com/Location/Location&maps/Scandinavia.php": [
          [
            "2013_20", 
            {
              "length": "3763", 
              "offset:": "122159591", 
              "filename": "https://aws-publicdatasets.s3.amazonaws.com/common-crawl/crawl-data/CC-MAIN-2013-20/segments/1368698238192/warc/CC-MAIN-20130516095718-00091-ip-10-60-113-184.ec2.internal.warc.gz"
            }
          ]
        ], 
        "http://hettahuskies.com/Location/When2come/w2cintro.php": [
          [
            "2013_20", 
            {
              "length": "7763", 
              "offset:": "124940270", 
              "filename": "https://aws-publicdatasets.s3.amazonaws.com/common-crawl/crawl-data/CC-MAIN-2013-20/segments/1368698411148/warc/CC-MAIN-20130516100011-00070-ip-10-60-113-184.ec2.internal.warc.gz"
            }
          ]
        ], 
        "http://hettahuskies.com/Location/Areaattractions/aaintro.php": [
          [
            "2013_20", 
            {
              "length": "4140", 
              "offset:": "123806691", 
              "filename": "https://aws-publicdatasets.s3.amazonaws.com/common-crawl/crawl-data/CC-MAIN-2013-20/segments/1368700212265/warc/CC-MAIN-20130516103012-00009-ip-10-60-113-184.ec2.internal.warc.gz"
            }
          ]
        ]
      }, 
      "query_crawl": ""
    }

For now this includes the full location of the source file, and the length and offset at which the data is located. For example to get the last entry (http://hettahuskies.com/Location/Areaattractions/aaintro.php) compute the data range as (offset, offset + length -1) and download using e.g. curl:

    $ curl -r 123806691-123810830 https://aws-publicdatasets.s3.amazonaws.com/common-crawl/crawl-data/CC-MAIN-2013-20/segments/1368700212265/warc/CC-MAIN-20130516103012-00009-ip-10-60-113-184.ec2.internal.warc.gz | \
    zcat | head -n 25

    WARC/1.0
    WARC-Type: response
    WARC-Date: 2013-05-21T16:36:12Z
    WARC-Record-ID: <urn:uuid:fa940850-e840-4dbc-9dda-8a12a983ea7f>
    Content-Length: 11265
    Content-Type: application/http; msgtype=response
    WARC-Warcinfo-ID: <urn:uuid:0e0dc031-834b-4214-8734-436e417840b7>
    WARC-Concurrent-To: <urn:uuid:1c9a8321-669c-44af-9d26-162048519f6d>
    WARC-IP-Address: 85.13.248.54
    WARC-Target-URI: http://hettahuskies.com/Location/Areaattractions/aaintro.php
    WARC-Payload-Digest: sha1:FJYCE63U6QKI5EH7N5NVMBQB2GJA4TRE
    WARC-Block-Digest: sha1:SBSHBG6E2ED3BPT5CU3QLMFLSF5WXF5G

    HTTP/1.0 200 OK
    Date: Tue, 21 May 2013 16:36:05 GMT
    Content-Type: text/html; charset=UTF-8
    Connection: close
    Server: Apache
    X-Powered-By: PHP/5.2.17

    <U+FEFF>

    <!DOCTYPE HTML PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dt
    d">
    <html [...]

Format is warc header, empty line, http response header, empty line, html content. Check out [download_candidates.py](https://github.com/ModernMT/DataCollection/blob/master/baseline/download_candidates.py) for downloading code in python using connection pools.

Results from the metadata API are limited to 10000 per request, just to keep the result size reasonable. It's not super fast but I assume that's because of either the python interface or, more likely, because we're touching many files over NFS. For batch processing we can access the DB locally and use the C++ interface. 

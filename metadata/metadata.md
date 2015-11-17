## Intro

For each page in CommonCrawl we hold as metadata

* The location of the raw download in S3. This is given as a URL plus offset and length.
* The languages discovered by CLD2 in the raw text of the page. This is given as a list of (Language / Number of bytes) pairs.

## Getting location data

Example: crawl 2015_40

For recent crawls we use the data files from the common crawl index. These are just 300 gzipped files containing key-value pairs.

```
mkdir 2015_40
cd 2015_40
for i in `seq -w 0 299`; do wget -c https://aws-publicdatasets.s3.amazonaws.com/common-crawl/cc-index/collections/CC-MAIN-2015-40/indexes/cdx-00${i}.gz; done
```
Restart the above until all files are completed.

## Building the Binaries for rocksdbs
```
cd ~/net/build
git clone git@github.com:facebook/rocksdb.git
cd rocksdb
PORTABLE=1 make shared_lib static_lib
```

## Building data database from location data

```
mkdir -p /home/buck/net/cc/meta/db/2015_40
pv 2015_40/cdx-00???.gz | \
gzip -cd | \
python ~/net/build/DataCollection/metadata/metadatabase.py --cdx 2015_40 cdx | \
/home/buck/net/build/DataCollection/metadata/rocksdb/insertkv /home/buck/net/cc/meta/db/2015_40/
```

## Running MetaData Server ##
Install pyrocksdb following these instructions: http://pyrocksdb.readthedocs.org/en/latest/installation.html
Instead of
```
	make shared_lib
```
Run
```
	PORTABLE=1 make shared_lib
```
as above to make the binary independent of the underlying CPU revision

Run the server with
```
/home/buck/net/build/DataCollection/metadata/md_server.py /PATH_TO_DBS/db/rdb_201*/ -ip 129.215.197.184 -port 8080
```
(change IP and Port)


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
gzip -9 > 2015_22.kv.gz
```

## Metadata API

The metadata API allows querying with a partial URL prefix and (optionally) a crawl name.

    $ curl "http://data.statmt.org:8080/query_prefix?url=hettahuskies&crawl=2013_20&pretty=1&max_results=2"
    {
      "query_path": "",
      "query_crawl": "2013_20",
      "locations": {
        "http://hettahuskies.com/": [
          {
            "filename": "https://aws-publicdatasets.s3.amazonaws.com/common-crawl/crawl-data/CC-MAIN-2013-20/segments/1368699684236/warc/CC-MAIN-20130516102124-00033-ip-10-60-113-184.ec2.internal.warc.gz",
            "length": "4194",
            "mime": "UNKNOWN",
            "offset": "127252350",
            "crawl": "2013_20"
          }
        ],
        "http://hettahuskies.com/Location/Areaattractions/aaintro.php": [
          {
            "filename": "https://aws-publicdatasets.s3.amazonaws.com/common-crawl/crawl-data/CC-MAIN-2013-20/segments/1368700212265/warc/CC-MAIN-20130516103012-00009-ip-10-60-113-184.ec2.internal.warc.gz",
            "length": "4140",
            "mime": "UNKNOWN",
            "offset": "123806691",
            "crawl": "2013_20"
          }
        ]
      },
      "query_domain": "hettahuskies",
      "db_key": "hettahuskies http://hettahuskies",
      "skipped_keys": []
    }

If 'crawl' is not specified, we get results from all crawls at once. Get a list by using the _crawls_ endpoint:

    $ curl "http://data.statmt.org:8080/crawls?pretty=1"
    {
      "crawls": [
        "2012",
        "2013_20",
        "2014_15",
        "2014_23",
        "2014_35",
        "2014_41",
        "2014_42",
        "2014_49",
        "2014_52",
        "2015_06",
        "2015_11",
        "2015_14",
        "2015_18",
        "2015_22",
        "2015_27"
      ]
    }


The 'locations' field hold url-location pairs the point into Amazon S3 where the full pages are stored. This includes the full location of the source file, and the length and offset at which the data is located. For example to get the last entry (http://hettahuskies.com/Location/Areaattractions/aaintro.php) compute the data range as (offset, offset + length -1) and download using e.g. curl:

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

Results from the metadata API are limited to 10000 per request by default, just to keep the result size reasonable. Set max_results to a higher value to increase this limit. For batch processing we can access the DB locally and use the C++ interface.

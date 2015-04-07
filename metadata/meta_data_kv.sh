#!/bin/bash

#$1 /fs/gna0/buck/cc/links
#$2 2013_20
#$3 1368701562534

# find $1/$2/$3/ | grep internal.links.gz | xargs zcat |\
zcat $1/$2/$3/*internal.links.gz | \
/home/buck/net/build/DataCollection/metadata/metadatabase.py $2 $3 | \
gzip -9 > $1/$2/$3/db_kv.gz
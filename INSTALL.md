Start with fresh Ubuntu Server 14.03.03 LTS

Check the raw version of this file for easy copy/paste

# Install packages
```
sudo apt-get update
sudo apt-get install build-essential git-core pkg-config
sudo apt-get install automake libtool
# for scipy
sudo apt-get install libxml2-dev libxslt1-dev
sudo apt-get install parallel
# python packages
sudo apt-get install python-dev python-pip python-virtualenv python-numpy python-scipy  ipython  python-nose
# for RocksDB
sudo apt-get install libgflags-dev libsnappy-dev libbz2-dev liblzma-dev zlib1g-dev libjsoncpp-dev
# Tools
sudo apt-get install pigz
```

# Make a directory for code
```
cd
mkdir -p net/build
```

# Clone project from github (add ssh key before)
```
cd net/build/
git clone git@github.com:ModernMT/DataCollection.git
```

# Make new virtualenv
```
cd net/build/
virtualenv crawl
```

# Activate virtualenv
```
source ~/net/build/crawl/bin/activate
```

# Install requirements
```
sudo apt-get install libffi-dev
sudo apt-get install libssl-dev
sudo apt-get install liblapack-dev
sudo apt-get install gfortran
cd DataCollection/
pip install --upgrade 'git+https://github.com/GregBowyer/cld2-cffi.git'
pip install -r requirements.txt
```

# Install moses
```
sudo apt-get install build-essential git-core pkg-config automake libtool
cd /home/build
git clone https://github.com/moses-smt/mosesdecoder moses
cd moses
make -f contrib/Makefiles/install-dependencies.gmake
```

# Install Bitextor

Like described at http://sourceforge.net/p/bitextor/wiki/Home/ (used 4.1.0-rc4 for baseline test, but newer versions should work)

Potentially needed option when configuring: `./configure --without-apertium`

Download `de-en.dict` from Bitextor sourceforge website.

## Running a baseline ##
```
cd
mkdir -p experiments/baseline/en-de
cd experiments/baseline/en-de
```

# Step 1: Produce candidate urls
```
curl http://www.statmt.org/~buck/mmt/langstat_kv/2015_27_kv.gz | gzip -cd | head -n 10000000 | nice python /home/buck/net/build/DataCollection/baseline/langstat2candidates.py -lang=de | sort -u -k 1,1 --compress-program=pigz > candidates.de
curl http://www.statmt.org/~buck/mmt/langstat_kv/2015_27_kv.gz | gzip -cd | head -n 10000000 | nice python /home/buck/net/build/DataCollection/baseline/langstat2candidates.py -lang=en -candidates candidates.de | sort -u -k 1,1 --compress-program=pigz > candidates.en-de
```
The `head` command should be removed when wanting to produce all candidate URLs from a crawl.

# Alternative: Run with gnu parallel to speed things up. Replace 'python' with 'parallel --block=200M --pipe -j 4 python'
```
curl http://www.statmt.org/~buck/mmt/langstat_kv/2015_27_kv.gz | gzip -cd | head -n 10000000 | nice parallel --block=200M --pipe -j 4 python /home/buck/net/build/DataCollection/baseline/langstat2candidates.py -lang=de | sort -u -k 1,1 --compress-program=pigz > candidates.de
curl http://www.statmt.org/~buck/mmt/langstat_kv/2015_27_kv.gz | gzip -cd | head -n 10000000 | nice parallel --block=200M --pipe -j 4 python /home/buck/net/build/DataCollection/baseline/langstat2candidates.py -lang=en -candidates candidates.de | sort -u -k 1,1 --compress-program=pigz > candidates.en-de
```
It probably doesn't make sense to run `parallel` with more jobs than processor cores (`-j 4`), you can also set `-j 0` that uses as many as possible (see GNU Parallel documentation http://www.gnu.org/software/parallel/man.html).

# Step 2: Look up where these URLs appear in S3
```
cat candidates.en-de | nice /home/buck/net/build/DataCollection/baseline/locate_candidates.py - - -server='http://statmt.org:8084/query_prefix' > candidates.en-de.locations
```

# Step 3: Download pages from S3 and extract text
```
cat candidates.en-de.locations | /home/buck/net/build/DataCollection/baseline/candidates2corpus.py -source_splitter='/home/buck/net/build/mosesdecoder/scripts/ems/support/split-sentences.perl -l en -b -q' -target_splitter='/home/buck/net/build/mosesdecoder/scripts/ems/support/split-sentences.perl -l de -b -q'  > en-de.down
```

# Step 4: Run Hunalign to extract parallel sentences

```
pv en-de.down | parallel --pipe /usr/local/bin/bitextor-align-segments --lang1 en --lang2 de -d de-en.dic > en-de.sent
```
When using `cat` instead of `pv` the machine might run out of memory.


## Building/Running MetaDataBase ##
see metadata/metadata.md

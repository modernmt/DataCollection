Start with fresh Ubuntu Server 14.03.03 LTS

# Install packages
sudo apt-get update
sudo apt-get install build-essential git-core pkg-config
# for scipy
sudo apt-get install libxml2-dev libxslt1-dev
sudo apt-get install parallel
# python packages
sudo apt-get install python-dev python-pip python-virtualenv python-numpy python-scipy  ipython  python-nose
# for RocksDB
sudo apt-get install libgflags-dev libsnappy-dev libbz2-dev liblzma-dev zlib1g-dev libjsoncpp-dev

# Make a directory for code
mkdir -p net/build

# Clone project from github (add ssh key before)
cd net/build/
git clone git@github.com:ModernMT/DataCollection.git

# Make new virtualenv
cd net/build/
virtualenv crawl

# Activate virtualenv
source ~/net/build/crawl/bin/activate

# Install requirements
cd DataCollection/
pip install -r requirements.txt


## Running a baseline ##
cd
mkdir -p experiments/baseline
cd experiments/baseline
curl http://www.statmt.org/~buck/mmt/langstat_kv/2015_27_kv.gz | gzip -cd | /usr/bin/parallel -j 4 --block=100M --pipe ~/net/build/DataCollection/baseline/langstat2candidates.py -lang de > candiates_de
curl http://www.statmt.org/~buck/mmt/langstat_kv/2015_27_kv.gz | gzip -cd | /usr/bin/parallel -j 4 --block=100M --pipe ~/net/build/DataCollection/baseline/langstat2candidates.py -lang en > candiates_en

## Building MetaDataBase ##
cd net/build/
git clone git@github.com:facebook/rocksdb.git
sudo apt-get install 
cd rocksdb
PORTABLE=1 make -j 4 all

# Optional: edit Makefile to point to directory where rocksdb was compiled
cd ~/net/build/DataCollection/metadata/rocksdb
make

## Running MetaData Server ##
Install pyrocksdb following these instructions: http://pyrocksdb.readthedocs.org/en/latest/installation.html
Instead of 
	make shared_lib
Run 
	PORTABLE=1 make -j 4 shared_lib
to make the binary independent of the underlying CPU revision



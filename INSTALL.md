# Hardware requirements

* CPU
  * Phase 1: 32 Core recommended (language identification in [Phase 1](metadata/metadata.md) takes about 100 days on such a 4 Core CPU, 32 Core CPU recommended)
  * Phase 2: 4 Core 
* RAM
  * 32 GB RAM (see issues #8 and #18)
* Drive space
  * Phase 1: 3-4 TB per Common Crawl
  * Phase 2: 300 GB per language direction

# Operating system requirements
The system was tested with Ubuntu 14.04 LTS, but other Debian-based Linux distributions should work as well.

# Software installation

## Install packages
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

## Make a directory for code
```
cd
mkdir -p net/build
```

## Clone project from github (add ssh key before)
```
cd net/build/
git clone git@github.com:ModernMT/DataCollection.git
```

## Make new virtualenv (optional)
```
cd net/build/
virtualenv crawl
```

## Activate virtualenv (optional)
```
source ~/net/build/crawl/bin/activate
```

## Install requirements
```
sudo apt-get install libffi-dev
sudo apt-get install libssl-dev
sudo apt-get install liblapack-dev
sudo apt-get install gfortran
cd DataCollection/
pip install --upgrade 'git+https://github.com/GregBowyer/cld2-cffi.git'
pip install -r requirements.txt
```
When encountering issues with installing NLTK data, you might have to hand-edit `DEFAULT_URL` in `/usr/lib/python2.7/dist-packages/nltk/downloader.py` from `http://nltk.googlecode.com/svn/trunk/nltk_data/index.xml` to `http://www.nltk.org/nltk_data/`.

## Install Moses
```
sudo apt-get install build-essential git-core pkg-config automake libtool
cd /home/build
git clone https://github.com/moses-smt/mosesdecoder moses
cd moses
make -f contrib/Makefiles/install-dependencies.gmake
```

## Install Bitextor

Like described at http://sourceforge.net/p/bitextor/wiki/Home/ (tested baseline with 4.1.0-rc4, but newer versions should work)

Potentially needed option when configuring: `./configure --without-apertium`

Download `de-en.dict` from Bitextor sourceforge website.



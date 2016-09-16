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
When encountering issues with installing NLTK data, you might have to hand-edit `DEFAULT_URL` in `/usr/lib/python2.7/dist-packages/nltk/downloader.py` from `http://nltk.googlecode.com/svn/trunk/nltk_data/index.xml` to `http://www.nltk.org/nltk_data/`.

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



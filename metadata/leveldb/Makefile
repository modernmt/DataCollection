CXXFLAGS = -O2 -Wall -fmessage-length=0

default: all

insertkv: insertkv.o
	$(CXX) -o $@ $^ -pg -L/home/buck/net/build/leveldb -ltcmalloc -lleveldb -lpthread -lsnappy -Wl,-rpath=/home/buck/net/build/leveldb 

updatekv: updatekv.o
	$(CXX) -o $@ $^ -pg -L/home/buck/net/build/leveldb -ltcmalloc -lleveldb -lpthread -lsnappy -ljsoncpp -Wl,-rpath=/home/buck/net/build/leveldb 


%.o : %.cpp *.h Makefile
	@echo "***" $< "***"
	$(CXX) $(CXXFLAGS) -I/home/buck/net/build/leveldb/include -c $< -o $@  

.PHONY : all clean
all:    insertkv updatekv

clean:
	rm -f insertkv updatekv

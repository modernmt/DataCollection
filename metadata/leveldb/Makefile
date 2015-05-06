CXXFLAGS = -O3 -mtune=native -Wall -fmessage-length=0

default: all

insertkv: insertkv.o
	$(CXX) -o $@ $^ -pg -ltcmalloc -lleveldb -lpthread -lsnappy 
#     $(LIBS) 

%.o : %.cpp *.h Makefile
	@echo "***" $< "***"
	$(CXX) $(CXXFLAGS) -c $< -o $@  

.PHONY : all clean
all:    insertkv

clean:
	rm -f insertkv

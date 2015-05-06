# gumbo-parser directory
# https://github.com/google/gumbo-parser
#GUMBO = /home/buck/net/build/gumbo

#CLD2 = /home/buck/net/build/cld2
CXXFLAGS =  -O3 -g -Wall -fmessage-length=0
#-I$(GUMBO)/include/ -I$(CLD2)/public
#LIBS = -L$(GUMBO)/lib/ -L$(CLD2)/internal

default: all

insertkv: insertkv.o
	$(CXX) -o $@ $^ -lleveldb -lpthread -lsnappy
#     $(LIBS) 

%.o : %.cpp *.h Makefile
	@echo "***" $< "***"
	$(CXX) $(CXXFLAGS) -c $< -o $@  

.PHONY : all clean
all:    insertkv

clean:
	rm -f insertkv

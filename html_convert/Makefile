# gumbo-parser directory
# https://github.com/google/gumbo-parser
GUMBO = /home/buck/net/build/gumbo

CLD2 = /home/buck/net/build/cld2
CXXFLAGS =	-O2 -g -Wall -fmessage-length=0 -std=c++11  -I$(GUMBO)/include/ -I$(CLD2)/public
LIBS = -L$(GUMBO)/lib/ -L$(CLD2)/internal

default: all

html2text: html2text.o
	$(CXX) -o $@ $^  $(LDFLAGS) -lgumbo -lidn -lcld2_full $(LIBS) 

%.o : %.cpp *.h Makefile
	@echo "***" $< "***"
	$(CXX) $(CXXFLAGS) -c $< -o $@  

.PHONY : all clean
all:	html2text

clean:
	rm -f html2text.o html2text

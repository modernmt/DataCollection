# gumbo-parser directory
# https://github.com/google/gumbo-parser
GUMBO = /home/buck/net/build/gumbo
CXXFLAGS =	-O2 -g -Wall -fmessage-length=0 -std=c++11  -I$(GUMBO)/include/
LIBS = -L$(GUMBO)/lib/

default: all

html2text: html2text.o
	$(CXX) -o $@ $^ -static $(LDFLAGS) -lgumbo $(LIBS)

%.o : %.cpp *.h Makefile
	@echo "***" $< "***"
	$(CXX) $(CXXFLAGS) -c $< -o $@  

.PHONY : all clean
all:	html2text

clean:
	rm -f html2text.o html2text

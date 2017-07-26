# -*- GNUMakefile -*-

GUMBO_SRC:= /home/buck/net/build/gumbo
GUMBO_INC:= ${GUMBO_SRC}/include
GUMBO_LIB:= ${GUMBO_SRC}/lib
CLD2_SRC := /home/buck/net/build/cld2
CLD2_INC := ${CLD2_SRC}/public
CLD2_LIB := ${CLD2_SRC}/internal
CLD2_VAR := cld2_full

CXXFLAGS := -O2 -flto -g -Wall -fmessage-length=0 -std=c++11
LDFLAGS  := -flto -O2 -static 
LIBS     := -L${GUMBO_LIB} -L${CLD2_LIB}

OBJS =		html2text.o langsplit.o
HEADERS =	*.h

default: all

TARGET =	html2text langsplit

html2text: html2text.o
	$(CXX) -o $@ $^ $(LDFLAGS) -L${GUMBO_LIB} -lgumbo

langsplit: langsplit.o
	$(CXX) -o $@ $^ $(LDFLAGS) -L${CLD2_LIB} -l${CLD2_VAR}

html2text.o : html2text.cpp *.h Makefile
	@echo "***" $< "***"
	$(CXX) $(CXXFLAGS) -c -I${GUMBO_INC} $< -o $@  

langsplit.o : langsplit.cpp *.h Makefile
	@echo "***" $< "***"
	$(CXX) $(CXXFLAGS) -c -I${CLD2_INC} $< -o $@  


.PHONY : all clean
all:	html2text langsplit

clean:
	rm -f $(OBJS) $(TARGET)

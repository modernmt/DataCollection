#!/usr/bin/env python
#-------------------------------------------------------------------
#Extract info for Mapped files.
#This info is used when downloading the files from Common Crawl. 
#-------------------------------------------------------------------

import codecs
import sys
import re
from os import listdir
from os.path import isfile, join
import gzip
import collections
import time


def cleanOfSpaces(myString):
    """Clean a string of trailing spaces"""
    
    myString=re.sub("^( )+","",myString)
    myString=re.sub("( )+$","",myString)
    return myString



def getURL(info):
    """It gets the record from Info record"""
    
    info=re.sub("^{","",info)
    info=re.sub("}$","",info)
    
    components=info.split("\",")
    urlComponent=components[0]
    urlComponent=re.sub("\"","",urlComponent)
    
    url,urlValue=urlComponent.split(":",1)
    urlValue=cleanOfSpaces(urlValue)
    
    return urlValue


def printInfo (resDict,fo) :
    """Print the info."""
    
    for url in resDict:
        fo.write(resDict[url]["sourceURL"]+"\t"+resDict[url]["sourceInfo"]+"\n")
        fo.write(resDict[url]["destURL"]+"\t"+resDict[url]["destInfo"]+"\n")
    
    

def getInfo(gzFP,resDict,ordDictMap,sLang,dLang,fl):
    """It Get the Info related to Extracted Candidates."""
    
    chunk=500000
    
    fi = gzip.open(gzFP, 'r')
    ordDictMapReversed={v: k for k, v in ordDictMap.items()}
    
    start = time.time()
    
    iLine=0
    for line in fi:
        iLine+=1
        if iLine%chunk==0 :
            end = time.time()
            duration=(end-start)/60
            fl.write("========Chunk "+str(chunk)+" duration:" +str(duration)+" minutes\n")
            
        line=line.rstrip()
        bsURL,timestamp,info=line.split(" ",2)
        url=getURL(info)
        if url in ordDictMap :
            resDict[url]["sourceURL"]=url
            resDict[url]["sourceInfo"]=info
        elif url in ordDictMapReversed :
            resDict[ordDictMapReversed[url]]["destURL"]=url
            resDict[ordDictMapReversed[url]]["destInfo"]=info
    fi.close()



def readMappingFile(mappingFile):
    """It reads the Mapping File in an Ordered Map"""
    
    dictMap = collections.OrderedDict()
    fi=codecs.open(mappingFile, "r", "utf-8")
    for line in fi:
        line=line.rstrip()
        sLink,dLink=line.split("\t")
        dictMap[sLink]=dLink
    fi.close()
    return dictMap



def getMappingFile (sLang,dLang) :
    return "OutputFiles/candidates-Mapped-"+sLang+"-"+dLang+".txt"

def getOutputFile (sLang,dLang) :
    return "OutputFiles/candidates-Info-"+sLang+"-"+dLang+".txt"

def getLogFile (sLang,dLang) :
    return "OutputFiles/run-"+sLang+"-"+dLang+".log"

def main():
    
    sLang=sys.argv[1]
    dLang=sys.argv[2]
    dIndex=sys.argv[3]
    
    #dIndex="FilesTest"
    
    print "Reading the mapping file"
    mappingFile=getMappingFile (sLang,dLang)
    ordDictMap=readMappingFile(mappingFile)
    
    
    print "Get the inflated files containing the index."
    gzipFiles= [ f for f in listdir(dIndex) if f.endswith(".gz")]
    
    print "Get the file Output "
    fileOutput=getOutputFile (sLang,dLang)
    
    print "Get the log file"
    fileLog=getLogFile(sLang,dLang)
    fl=codecs.open(fileLog, "a", "utf-8")
    
    
    fl.write("\nStart Candidate Info Extraction\n")
    fo=codecs.open(fileOutput, "w", "utf-8")
    resDict={urlS:{} for urlS in ordDictMap}
    for gzipFile in gzipFiles:
        fl.write("Process "+gzipFile +"\n")
        gzFP=dIndex+"/"+gzipFile
        getInfo(gzFP,resDict,ordDictMap,sLang,dLang,fl)
    printInfo (resDict,fo)    
    fl.write("Results in:"+fileOutput+"\n")
    
    fo.close()
    fl.close()

    


if __name__ == '__main__':
  main()    
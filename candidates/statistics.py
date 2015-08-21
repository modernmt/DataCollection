#!/usr/bin/env python
#-------------------------------------------------------------------------------------------------
#Get useful information from the Mapped candidates Info.
#Like: What is the frequence of archives.How many mapped files are per archive.
#The archive with most mapping files.
#Which domains are more promising to Crawl Offline.
#-------------------------------------------------------------------------------------------------
import codecs
import sys
import re
from operator import itemgetter

def normalize(testURL):
    """Normalize the URL."""
    
    testURL=re.sub("^http(s)?://","",testURL)
    testURL=re.sub("/$","",testURL)
    components=testURL.split('/')
    return components


def getDictDomains(infoFile):
    """Compute the frequencies of domains to find the most profitable domains."""
    
    domainDict={}
    fi=codecs.open(infoFile, "r", "utf-8")
    for line in fi:
        line=line.rstrip()
        url,info=line.split("\t")
        
        components=normalize(url)
        domain=components[0]
        
        domainDict.setdefault(domain,0)
        domainDict[domain]+=1    
    fi.close()
    
    return domainDict


def cleanOfSpaces(myString):
    """Clean a string of trailing spaces"""
    
    myString=re.sub("^( )+","",myString)
    myString=re.sub("( )+$","",myString)
    return myString


def getWarcLocation(info):
    """It gets the warc location"""
    
    info=re.sub("^{","",info)
    info=re.sub("}$","",info)
    
    components=info.split("\",")
    warcComponent=components[-1]
    warcComponent=re.sub("\"","",warcComponent)
    
    fileName,warcValue=warcComponent.split(":",1)
    warcValue=cleanOfSpaces(warcValue)
    
    return warcValue


def getWarcDistribution(infoFile):
    """ Get the warc location frequencies"""
    
    warcDict={}
    fi=codecs.open(infoFile, "r", "utf-8")
    for line in fi:
        line=line.rstrip()
        url,info=line.split("\t")
        warcL=getWarcLocation(info)

        warcDict.setdefault(warcL,0)
        warcDict[warcL]+=1    
    fi.close()
    
    return warcDict


def printDistribution(fDict,fOutput):
    """It prints a particular distribution"""
    
    sDict=sorted(fDict.iteritems(), key=itemgetter(1), reverse=True)
    fo=codecs.open(fOutput, "w", "utf-8")
    
    for tup in sDict :
        fo.write(tup[0]+"\t"+str(tup[1])+"\n")
    
    fo.close()

def computeDomainDistribution(sLang,dLang,fl):
    """Computes the domain distribution """
    
    
    infoFile=getInputFile(sLang,dLang)
    domainDict=getDictDomains(infoFile)
    
    fDomain=getDomainFile (sLang,dLang)
    fl.write ("=====>In "+fDomain+"\n")
    printDistribution(domainDict,fDomain)
   
   
    
def computeWarcDistribution(sLang,dLang,fl):
    """Computes the warc distribution """
    
    infoFile=getInputFile(sLang,dLang)
    warcDict=getWarcDistribution(infoFile)
    
    fWarc=getWarcFile (sLang,dLang)
    fl.write ("=====>In "+fWarc+"\n")
    printDistribution(warcDict,fWarc)


def getInputFile (sLang,dLang) :
    return "OutputFiles/candidates-Info-"+sLang+"-"+dLang+".txt"

def getDomainFile (sLang,dLang) :
    return "OutputFiles/statistics-Domain-"+sLang+"-"+dLang+".txt"

def getWarcFile (sLang,dLang) :
    return "OutputFiles/statistics-Warc-"+sLang+"-"+dLang+".txt"


def getLogFile (sLang,dLang) :
    return "OutputFiles/run-"+sLang+"-"+dLang+".log"



def main():
    
    sLang=sys.argv[1]
    dLang=sys.argv[2]
    
    fileLog=getLogFile(sLang,dLang)
    fl=codecs.open(fileLog, "a", "utf-8")
    
    fl.write("\nStatistics\n")
    fl.write("Warc Distribution\n")
    computeWarcDistribution(sLang,dLang,fl)
    
    
    fl.write("Domain distribution\n")
    computeDomainDistribution(sLang,dLang,fl)

    
    fl.close()
    

if __name__ == '__main__':
  main()    
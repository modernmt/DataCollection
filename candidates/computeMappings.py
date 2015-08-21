#!/usr/bin/env python
#--------------------------------------------------------------------------------------
#This script is run after  the script that extracts candidates .
#It find the mapping between the candidates extracted in the previous step .
#--------------------------------------------------------------------------------------
import codecs
import sys
import re


def normalize(testURL):
    """Normalize the URL."""
    
    testURL=re.sub("^http(s)?://","",testURL)
    testURL=re.sub("/$","",testURL)
    components=testURL.split('/')
    return components



def getReplacedCandidates2(candDestList,sLang,dLang):
    """Get the target Candidates replaced with the Source Language code using rule 1:mi0064_en.htm====>mi0064_it.htm"""
    
    replDict={}
    for filePathD in candDestList:
            
            #---------1. Replace the Final File---------
            toReplace=dLang+"\.htm(l?)$"
            withReplace=sLang+".htm\\1"
            filePathR=re.sub(toReplace,withReplace,filePathD)
            
            #---------2. Replace the rest of the path-------------
            toReplace="([^A-Za-z]){1}"+dLang+"([^A-Za-z]){1}"
            withReplace="\\1"+sLang+"\\2"
            filePathR=re.sub(toReplace,withReplace,filePathR)
            
            replDict[filePathD]=filePathR
    return replDict





#(http://www.alno.ae/alnosys3/384.0.it.html, www.alno.ae/alnosys3, 384.0.it.html, 1, 0)
def mapCandidates2(candidatesDict,sLang,dLang):
    
    """Map the Candidates using rule 2:
    http://www.rhi.at/en/corporate_news_query_2011_en.html=>http://www.rhi.at/it/corporate_news_query_2011_it.html
    or
    http://www.rhi.at/en/corporate_news_query_2011.html=>http://www.rhi.at/it/corporate_news_query_2011.html
    """
    
    mapDict={}
    for domain in candidatesDict:
        tupleList=candidatesDict[domain].keys()
        candDestList=[tupleD[0] for tupleD in tupleList if tupleD[4]=='1' and candidatesDict[domain][tupleD]=='D']
        replDict=getReplacedCandidates2(candDestList,sLang,dLang)
        
        allFilesDomain=[tupleD[0] for tupleD in tupleList]
        for (fileS,fileR) in replDict.items():
            if fileR in allFilesDomain :
                indexS=allFilesDomain.index(fileS)
                indexR=allFilesDomain.index(fileR)
                mapDict[fileR]=fileS
    return mapDict    


def getReplacedCandidates1(candTupleList,sLang,dLang):
    """Get the target Candidates replaced with the Source Language code using rule 1:mi0064_en.htm====>mi0064_it.htm"""
    
    tupleReplacedList=[]
    toReplace=withReplace=""
    for dTuple in candTupleList:
        fileD=dTuple[2]
        if re.search("\.htm(l?)$",fileD) : 
            toReplace=dLang+"\.htm(l?)$"
            withReplace=sLang+".htm\\1"
        else :
            toReplace="="+dLang
            withReplace="="+sLang
        fileR=re.sub(toReplace,withReplace,fileD)    
        if fileR!=fileD :
            tup=(dTuple[0],dTuple[1],dTuple[2],dTuple[3],dTuple[4],fileR)
            tupleReplacedList.append(tup)
    return  tupleReplacedList   
 


#(http://www.alno.ae/alnosys3/384.0.it.html, www.alno.ae/alnosys3, 384.0.it.html, 1, 0)
def mapCandidates1(candidatesDict,sLang,dLang):
    """Map the Candidates using rule 1:mi0064_en.htm====>mi0064_it.htm"""
    
    mapDict={}
    for domain in candidatesDict:
        tupleList=candidatesDict[domain].keys()
        candDestList=[tupleD for tupleD in tupleList if tupleD[3]=='1' and candidatesDict[domain][tupleD]=='D']
        sourceList=[tupleD for tupleD in tupleList if tupleD[3]=='1' and candidatesDict[domain][tupleD]=='S']
        tupleReplacedList=getReplacedCandidates1(candDestList,sLang,dLang)
        for tupleR in tupleReplacedList:
            for tupleS in sourceList:
                if tupleR[5]==tupleS[2] and tupleR[1]==tupleS[1] :
                    mapDict[tupleS[0]]=tupleR[0]
    return mapDict    


def printCandidates (mapDict,fo) :
    """Print the candidates. """
    for linkS,linkD in mapDict.items():
        fo.write(linkS+"\t"+linkD+"\n")
    
    

#(http://www.alno.ae/alnosys3/384.0.it.html, www.alno.ae/alnosys3, 384.0.it.html, 1, 0)
def mapCandidates(candidatesDict,sLang,dLang,fl,fileGz):
    """Map the Candidates using all the rules"""
    
    
    mapDict1=mapCandidates1(candidatesDict,sLang,dLang)
    mapDict2=mapCandidates2(candidatesDict,sLang,dLang)
    mapDict=combineDictionaries(mapDict1,mapDict2)
    sizeFinal=len(mapDict)
    fl.write (fileGz+" mapped: "+str(sizeFinal)+"\n")
    
    return mapDict


def combineDictionaries(mapDict1,mapDict2):
    """Combine dictionaries giving priority to rule2 over rule1"""
    
    mapDict=dict(mapDict2)
    for (fileS,fileD) in mapDict1.items():
        if fileS not in mapDict.keys() and fileD not in mapDict.values():
            mapDict[fileS]=fileD
    return mapDict

def nonblank_lines(f):
    for l in f:
        line = l.rstrip()
        if line:
            yield line

def readCandidates(fi):
    """It reads the final candidate list for each file."""
    
    candidatesDict={}
    for line in fi :
        line=line.rstrip()
        if re.search('^-+',line) :
            linii,fileGz=line.split("\t")
            yield candidatesDict,fileGz
            candidatesDict={}
        else :
            lineComponents=line.split("\t")
            flag,link=lineComponents[0].split("#:",1)
            
            urlComponents=normalize(link)
            domain=urlComponents[0]
            finalFile=urlComponents[-1]
            urlComponents.pop()
            path="/".join(urlComponents)
            if domain not in candidatesDict :
                candidatesDict[domain]={}
            tup=(link,path,finalFile,lineComponents[1],lineComponents[2])
            candidatesDict[domain][tup]=flag
        
    fi.close()
  


def getCandidateFile (sLang,dLang) :
    return "OutputFiles/candidates-"+sLang+"-"+dLang+".txt"


def getLogFile (sLang,dLang) :
    return "OutputFiles/run-"+sLang+"-"+dLang+".log"
    


def getOutputFile (sLang,dLang) :
    return "OutputFiles/candidates-Mapped-"+sLang+"-"+dLang+".txt"




def main():
    
    sLang=sys.argv[1]
    dLang=sys.argv[2]
    
    fileCandidates=getCandidateFile (sLang,dLang)
    fileOutput=getOutputFile (sLang,dLang)
    
    fo=codecs.open(fileOutput, "w", "utf-8")
    
    fileLog=getLogFile(sLang,dLang)
    fl=codecs.open(fileLog, "a", "utf-8")
    fl.write("\nCompute Mappings\n")
    
    #fileCandidates="candidates-Test.txt"
    
    fl.write ("Load Candidates (in gzFile steps) from:"+fileCandidates+"\n")
    with codecs.open(fileCandidates, "r", "utf-8") as fi:
        for candidatesDict,fileGz in readCandidates(fi) :
            mapDict=mapCandidates(candidatesDict,sLang,dLang,fl,fileGz)
            printCandidates(mapDict,fo)
    
    fl.write ("Candidates Printed in "+fileOutput+"\n")
    
    fo.close()
    fl.close()
    
    
    
if __name__ == '__main__':
  main()    


#!/usr/bin/env python
#----------------------------------------------------------------------------------
#It extracts candidate sites applying some simple rules.
#----------------------------------------------------------------------------------

import codecs
import sys
import re
from os import listdir
from os.path import isfile, join
import gzip


def cleanOfSpaces(myString):
    """Clean a string of trailing spaces"""
    
    myString=re.sub("^( )+","",myString)
    myString=re.sub("( )+$","",myString)
    return myString


def normalize(testURL):
    """Normalize the URL."""
    
    testURL=re.sub("^http(s)?://","",testURL)
    testURL=re.sub("/$","",testURL)
    components=testURL.split('/')
    return components

def isHTML (fileS):
    """If the last file ends with HTML"""
    
    if fileS.endswith("htm") or fileS.endswith("html") :
        return 1
    return 0

def hasLangParameter(lang,fileS):
    """It has the lang parameter in the form: lang=en etc.  """
    if re.search ("="+lang,fileS) :
        return 1
    


def rule1(url,lang):
    """The rule says that the destination file should be same after replacing the language code: mi0064_en.htm====>mi0064_it.htm
    or it should have the structure of type =en"""
    
    components=normalize(url)
    fileS=components[-1]
    if isHTML (fileS) :
        regex="([^A-Za-z])"+lang+"\\.htm(l?)$"
        m=re.search(regex,fileS)
        if m:
            return 1
    elif hasLangParameter(lang,fileS) :
        return 1
    return 0


def rule2(url,lang):
    """The rule says that the path to the file should differ by a language code e.g www.cvc.com/en/ => www.cvc.com/it/  """
    
    components=normalize(url)
    components.pop()
    urlPart="/".join(components)
    regex="([^A-Za-z]){1}"+lang+"([^A-Za-z]){1}"
    m=re.search(regex,urlPart)
    if m :
        return 1
    return 0



def rulesOn (url,lang):
    """If the URL has a certain form I say I have a promising URL."""
    
    mapRes={}
    
    res1=rule1(url,lang)
    res2=rule2(url,lang)
    
    mapRes["rule1"]=res1
    mapRes["rule2"]=res2
    
    return mapRes


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
    

def getCandidates(gzFP,fo,sLang,dLang):
    """Check if a url could be a candidate or not."""
    
    fi = gzip.open(gzFP, 'r')
    
    nCandidates=0
    for line in fi:
        line=line.rstrip()
        bsURL,timestamp,info=line.split(" ",2)
        url=getURL(info)
        
        mapS=rulesOn(url,sLang)
        mapD=rulesOn (url,dLang)
        
        #---------If-Elif to impede that the same link is put under both source and destination----------- 
        if mapS["rule1"] or mapS["rule2"]:
            nCandidates+=1
            fo.write("S#:"+url+"\t"+str(mapS["rule1"])+"\t"+str(mapS["rule2"])+"\n")
        elif mapD["rule1"] or mapD["rule2"] :
            nCandidates+=1
            fo.write("D#:"+url+"\t"+str(mapD["rule1"])+"\t"+str(mapD["rule2"])+"\n")
    
    fi.close()
    fo.write("-------------\t"+gzFP+"\n")
    return nCandidates
    


def getFileOutput (sLang,dLang) :
    return "OutputFiles/candidates-"+sLang+"-"+dLang+".txt"
    
def getLogFile (sLang,dLang) :
    return "OutputFiles/run-"+sLang+"-"+dLang+".log"
    
    
def main():
    
    sLang=sys.argv[1]
    dLang=sys.argv[2]
    dIndex=sys.argv[3]
    
    print "Get the inflated files containing the index."
    gzipFiles= [ f for f in listdir(dIndex) if f.endswith(".gz")]
    
    print "Get the file Output "
    fileOutput=getFileOutput (sLang,dLang)
    
    print "Get Log File"
    fileLog=getLogFile (sLang,dLang)
    
    
    fl=codecs.open(fileLog, "w", "utf-8")
    fl.write("Start Candidate Extraction\n")
    fo=codecs.open(fileOutput, "w", "utf-8")
    for gzipFile in gzipFiles:
        gzFP=dIndex+"/"+gzipFile
        nCandidates=getCandidates(gzFP,fo,sLang,dLang)
        fl.write (gzipFile +":"+str(nCandidates)+"\n")
    fl.write("End Candidate Extraction\n")
    
    fo.close()
    fl.close()



if __name__ == '__main__':
  main()    
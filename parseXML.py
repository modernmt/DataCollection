#!/usr/bin/env python
#--------------------------------------------------------------------------------------
#Parse the xml to extract the title and the URL of the crawled web pages by ILSP Crawler.
#--------------------------------------------------------------------------------------
import xml.etree.ElementTree as ET
from os import listdir
from os.path import isfile, join
import re
import codecs
import sys

def getInfo(xmlFile):
    """It gets the title and the URL of the crawled by ILSP Crawler."""
    
    ns = {'schema': 'http://www.xces.org/schema/2003'}
    tree = ET.parse(xmlFile)
    root = tree.getroot()
    
    sourceDesc=root[0][0][2]
    title=sourceDesc[0][0][0]
    eAddress=sourceDesc[0][0][2][3]
    
    
    titleText=title.text
    eAddressText=eAddress.text
    
    if (titleText is None) :
        titleText=""
    if (eAddressText is None) :
        eAddressText=""
        
    return titleText,eAddressText    


def isXMLParsedFile(fileCheck):
    """The xml file that all HTML files are transformed to  have a number followed by .xml (e.g 61.xml)"""
    return re.search(r'^\d+\.xml$',fileCheck)


def isXMLMappedFile(fileCheck):
    """The xml file with that contains the mapping (e.g 59_12_m.xml)"""
    return re.search(r'_[a-z]+.xml$',fileCheck)



def getXMLFiles (directory) :
    "It gets the list of files for which I need to take the title and the address."
    
    allFiles = [ f for f in listdir(directory) if isfile(join(directory,f))]
    xmlParsedList=[ f for f in allFiles if isXMLParsedFile(f)]
    xmlMappedList=[ f for f in allFiles if isXMLMappedFile(f)]
    
    return xmlParsedList,xmlMappedList
    
def getMapping (fileMapped) :
    """Get the mapping between files from the file name."""
    
    fileRes=re.sub("_[a-z]+\.xml$","",fileMapped)
    fileS,fileD=fileRes.split("_")
    
    fileS+=".xml"
    fileD+=".xml"
    
    return fileS,fileD 
    

def printMapping (xmlMappedList,fileOutput) :
    """Print the Mapping"""
    
    xmlMapingList=[ getMapping(f) for f in xmlMappedList]
    fo= codecs.open(fileOutput, "a", "utf-8")
    fo.write("\nFiles Mapped:\n")
    fo.write("-----------------------------------------------------\n")
    for mapPair in xmlMapingList :
        fo.write (mapPair[0]+"\t"+mapPair[1]+"\n")
        
    fo.close()    
   
def printDownloaded (xmlParsedList,fileOutput,directory) :
    """Print the downloaded files """
    
    fo= codecs.open(fileOutput, "a", "utf-8")
    fo.write("Files Downloaded:\n")
    fo.write("-----------------------------------------------------\n")
    for xmlFile in xmlParsedList:
        xmlPath=join(directory,xmlFile)
        title,url=getInfo(xmlPath)
        fo.write(xmlFile+"\t"+title+"\t"+url+"\n")
    fo.close()
    
    
def main():
    
    print "Read the xml files"
    directory=sys.argv[1]
    fileOutput=sys.argv[2]
    
    
    xmlParsedList,xmlMappedList=getXMLFiles (directory)
    print "Get the Title and the web address of the crawled pages by ILFSP Crawler."
    fo= codecs.open(fileOutput, "w", "utf-8")
    fo.close()
    
    printDownloaded (xmlParsedList,fileOutput,directory)
    printMapping (xmlMappedList,fileOutput)
    
    print "Done"
    
    
    
if __name__ == '__main__':
  main()
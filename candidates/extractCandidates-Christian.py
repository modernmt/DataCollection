#!/usr/bin/env python
#-------------------------------------------------------------------------
# It extracts candidate sites applying some simple rules.
# This script works with Christian's file format.
#-------------------------------------------------------------------------

import codecs
import sys
import re


def cleanOfSpaces(myString):
    """Clean a string of trailing spaces"""

    myString = re.sub("^( )+", "", myString)
    myString = re.sub("( )+$", "", myString)
    return myString


def normalize(testURL):
    """Normalize the URL."""

    testURL = re.sub("^http(s)?://", "", testURL)
    testURL = re.sub("/$", "", testURL)
    components = testURL.split('/')
    return components


def isHTML(fileS):
    """If the last file ends with HTML"""

    if fileS.endswith("htm") or fileS.endswith("html"):
        return 1
    return 0


def hasLangParameter(lang, fileS):
    """It has the lang parameter in the form: lang=en etc.  """
    if re.search("=" + lang, fileS):
        return 1


def rule1(url, lang):
    """The rule says that the destination file should be same after replacing the language code: mi0064_en.htm====>mi0064_it.htm
    or it should have the structure of type =en"""

    components = normalize(url)
    fileS = components[-1]
    if isHTML(fileS):
        regex = "([^A-Za-z])" + lang + "\\.htm(l?)$"
        m = re.search(regex, fileS)
        if m:
            return 1
    elif hasLangParameter(lang, fileS):
        return 1
    return 0


def rule2(url, lang):
    """The rule says that the path to the file should differ by a language code e.g www.cvc.com/en/ => www.cvc.com/it/  """

    components = normalize(url)
    components.pop()
    urlPart = "/".join(components)
    regex = "([^A-Za-z]){1}" + lang + "([^A-Za-z]){1}"
    m = re.search(regex, urlPart)
    if m:
        return 1
    return 0


def rulesOn(url, lang):
    """If the URL has a certain form I say I have a promising URL."""

    mapRes = {}

    res1 = rule1(url, lang)
    res2 = rule2(url, lang)

    mapRes["rule1"] = res1
    mapRes["rule2"] = res2

    return mapRes


def getURL(line):
    """It gets the record from the line provided"""

    rest, json = line.split("\t")
    components = re.split("\s+", rest)
    for component in components:
        if re.search("^http(s)?://", component):
            return component


def getCandidates(fi, fo, sLang, dLang):
    """Check if a url could be a candidate or not."""

    nCandidates = 0
    for line in fi:
        line = line.rstrip()

        # tld url crawl<TAB>json_data
        url = getURL(line)

        mapS = rulesOn(url, sLang)
        mapD = rulesOn(url, dLang)

        #---------If-Elif to impede that the same link is put under both source
        if mapS["rule1"] or mapS["rule2"]:
            nCandidates += 1
            fo.write(
                "S#:" + url + "\t" + str(mapS["rule1"]) + "\t" + str(mapS["rule2"]) + "\n")
        elif mapD["rule1"] or mapD["rule2"]:
            nCandidates += 1
            fo.write(
                "D#:" + url + "\t" + str(mapD["rule1"]) + "\t" + str(mapD["rule2"]) + "\n")

    return nCandidates


def getFileOutput(dOutput, sLang, dLang):
    return dOutput + "/candidates-" + sLang + "-" + dLang + ".txt"


def getLogFile(dOutput, sLang, dLang):
    return dOutput + "/run-" + sLang + "-" + dLang + ".log"


def main():

    sLang = sys.argv[1]
    dLang = sys.argv[2]

    getCandidates(sys.stdin, sys.stdout, sLang, dLang)


if __name__ == '__main__':
    main()

#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import re
import urlparse


def process_buffer(buffer):
    if not buffer or len(buffer) < 2:
        return
    buffer = [line.decode('utf-8', 'ignore') for line in buffer]
    split_buffer = [line.strip().lower().split("\t")
                    for line in buffer]
    if list(set(map(len, split_buffer))) != [4]:
        for line in buffer:
            sys.stderr.write(line.encode('utf-8'))
        return
    original_urls = []
    stripped_languages = []
    detected_languages = []
    for stripped_url, \
            original_url, \
            stripped_language, \
            detected_language in split_buffer:
        original_urls.append(original_url)
        stripped_languages.append(stripped_language)
        detected_languages.append(detected_language)

    if len(set(original_urls)) < 2:
        # print "not enough urls"
        return
    if len(set(stripped_languages)) < 2:
        # print "not enough stripped languages", languages_stripped
        return
    if len(set(detected_languages)) < 2:
        # print "not enough detected_languages", detected_languages
        return

    for language in stripped_languages:
        for detected_language in detected_languages:
            # print "looking for ", language, " in ", detected_languages
            if language in detected_language.replace("chineset", "chinese") \
                                            .split('/'):
                for line in buffer:
                    sys.stdout.write(line.encode("utf-8"))
                return


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()

    buffer = []
    buffer_url = None
    for line in sys.stdin:
        # line = line.decode("utf-8", "ignore")
        url = line.split("\t", 1)[0]
        if url != buffer_url:
            process_buffer(buffer)
            buffer = [line]
            buffer_url = url
        else:
            buffer.append(line)
            # print url != buffer_url
    process_buffer(buffer)

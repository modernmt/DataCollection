import sys
import subprocess
import os
import threading
from nltk.tokenize import wordpunct_tokenize
import re


class SpaceTokenizer(object):

    """ Fall-back is no tokenizer is available """

    def __init__(self):
        sys.stderr.write("Using SpaceTokenizer.\n")

    def process(self, line):
        return " ".join(line.split())


class WordPunctTokenizer(object):

    """ Fall-back is no tokenizer is available """

    def __init__(self):
        sys.stderr.write("Using WordPunctTokenizer.\n")

    def process(self, line):
        words = [w for w in wordpunct_tokenize(
            line) if re.match("\w+|\d+", w) is not None]
        return " ".join(words)


class ExternalProcessor(object):

    """ wraps an external script and does utf-8 conversions, is thread-safe """

    def __init__(self, cmd):
        self.cmd = cmd
        self.devnull = open(os.devnull, 'wb')
        self._lock = threading.Lock()
        self.proc = None
        self.reset()

    def reset(self):
        with self._lock:
            if self.proc is not None:
                res = self.proc.communicate()
                if res[0].strip():
                    sys.stderr.write("Remaining output: %s" % res[0])
            self.proc = subprocess.Popen(self.cmd.split(),
                                         stdin=subprocess.PIPE,
                                         stdout=subprocess.PIPE,
                                         stderr=self.devnull)

    def process_multiline(self, text):
        res = []
        for line in text.split(u'\n'):
            if line.strip():
                res.append(self.process(line))
        return u'\n'.join(res)

    def process(self, line):
        if self.cmd is None or not line.strip():
            return line
        assert u"\n" not in line
        u_string = u"%s\n" % line
        u_string = u_string.encode("utf-8")
        result = u_string  # fallback: return input
        with self._lock:
            self.proc.stdin.write(u_string)
            self.proc.stdin.flush()
            result = self.proc.stdout.readline()
        self.reset()
        return result.decode("utf-8").strip()

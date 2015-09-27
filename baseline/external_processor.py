import os
import subprocess
import threading


class ExternalProcessor(object):

    """ wraps an external script and does utf-8 conversions, is thread-safe """

    def __init__(self, cmd):
        self.cmd = cmd
        self.devnull = open(os.devnull, 'wb')
        if self.cmd is not None:
            self.proc = subprocess.Popen(cmd.split(), stdin=subprocess.PIPE,
                                         stdout=subprocess.PIPE,
                                         stderr=self.devnull)
            self._lock = threading.Lock()

    def process(self, line):
        if self.cmd is None or not line.strip():
            return line
        u_string = u"%s\n" % line
        u_string = u_string.encode("utf-8")
        result = u_string  # fallback: return input
        with self._lock:
            self.proc.stdin.write(u_string)
            self.proc.stdin.flush()
            result = self.proc.stdout.readline()
        return result.decode("utf-8").strip()


class TextProcessor(object):

    def __init__(self, splitter=None, tokenizer=None):
        self.split_cmd = splitter
        self.tokenizer = None
        if tokenizer:
            self.tokenizer = ExternalProcessor(tokenizer)

    def split_sentences(self, text):
        if not text:
            return []
        p = subprocess.Popen(self.split_cmd.split(), stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE)
        out, err = p.communicate(input=text.encode("utf-8") + "\n")
        return out.decode("utf-8").split("\n")

    def sentences(self, text):
        if text:
            if self.split_cmd:
                text = self.split_sentences(text)
            else:
                text = [text]
            for line in text:
                if not line.strip():
                    continue
                if self.tokenizer:
                    yield self.tokenizer.process(line).strip()
                else:
                    yield line.strip()

    def process(self, text):
        return "\n".join(
            (line for line in self.sentences(text) if line.strip()))

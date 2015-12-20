import os
import subprocess
import threading
import logging


class ExternalTextProcessor(object):

    def __init__(self, cmd):
        self.cmd = cmd
        self.proc = None
        self.output = u""

    def process(self, text, timeout=60.0):
        # timeout in seconds
        assert isinstance(text, unicode)

        def target():
            self.proc = subprocess.Popen(self.cmd,
                                         stdin=subprocess.PIPE,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE,
                                         shell=True)
            if not self.input.endswith('\n'):
                self.input += "\n"
            self.output = self.proc.communicate(
                input=self.input.encode('utf-8'))[0].decode('utf-8')

        self.input = text

        thread = threading.Thread(target=target)
        thread.start()

        thread.join(timeout)

        if thread.is_alive():
            logging.warning('Terminating process after %f seconds' % timeout)
            logging.warning("failed for '%s'" % repr(text))
            logging.warning("command: %s" % repr(self.cmd))
            self.proc.kill()
            thread.join()
        return self.output


class ExternalLineProcessor(object):

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
        assert isinstance(line, unicode), 'Expecting unicode input\n'
        assert '\n' not in line, 'Expecting a single line; found newline\n'
        if not line.strip():
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
            self.tokenizer = ExternalLineProcessor(tokenizer)

    def split_sentences(self, text):
        proc = ExternalTextProcessor(self.split_cmd.split())
        output = proc.process(text.replace("\n", "\n\n"))

        for line in output.split("\n"):
            line = line.strip()
            if not line or line == "<P>":
                continue
            yield line

        # if not text:
        #     return []

        # p = subprocess.Popen(self.split_cmd.split(), stdin=subprocess.PIPE,
        #                      stdout=subprocess.PIPE)
        # out, err = p.communicate(input=text.encode("utf-8") + "\n")
        # return out.decode("utf-8").split("\n")

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
        # text is unicode
        assert isinstance(text, unicode), "Expecting unicode input"
        return "\n".join(
            (line for line in self.sentences(text) if line.strip()))

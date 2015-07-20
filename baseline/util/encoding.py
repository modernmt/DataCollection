import chardet
from chardet.universaldetector import UniversalDetector

def guess_encoding_incremental(data):
    sys.stderr.write("running incremental chardet\n")
    detector = UniversalDetector()
    for line in data.split("\n"):
        detector.feed(line)
        if detector.done:
            break
    detector.close()
    encoding = detector.result
    return encoding["encoding"]


def guess_encoding(data):
    sys.stderr.write("running full chardet\n")
    encoding = chardet.detect(data)
    return encoding["encoding"]


def convert_to_utf8(data, force_chardet=False):
    encoding = "utf-8"
    try:
        if force_chardet:
            raise
        data = data.decode(encoding)
    except:
        encoding = guess_encoding_incremental(data)
        try:
            data = data.decode(encoding)
        except:
            encoding = guess_encoding(data)
            try:
                data = data.decode(encoding)
            except:
                sys.stderr.write("Fallback: ignoring errors.\n")
                return data.decode("utf-8", errors='ignore')
    # sys.stderr.write("Detected encoding: %s\n"
    #                  % encoding)
    return data


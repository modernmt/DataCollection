import base64
import gzip
import sys
from collections import namedtuple, defaultdict
import cPickle as pickle
sys.path.append("/home/buck/net/build/DataCollection/baseline")
from textsanitzer import TextSanitizer
from external_processor import ExternalTextProcessor
from tokenizer import ExternalProcessor, SpaceTokenizer, WordPunctTokenizer


# Page = namedtuple(
#     "Page", "url, html, text, mime_type, encoding, french, english, english_mt")

magic_number = "df6fa1abb58549287111ba8d776733e9"


class Page(object):

    def __init__(self, url, html, text, mime_type, encoding, french, english, english_mt):
        self.url = url
        self.html = html
        self.text = text
        self.mime_type = mime_type
        self.encoding = encoding
        self.french = french
        self.english = english
        self.english_mt = english_mt

    def __str__(self):
        res = []
        res.append("--Page--")
        res.append("url : %s" % self.url)
        res.append("html : %s" % self.html)
        res.append("text : %s" % self.text.encode('utf-8'))
        res.append("mime_type : %s" % self.mime_type)
        res.append("encoding : %s" % self.encoding)
        res.append("french : %s" % self.french.encode('utf-8'))
        res.append("english : %s" % self.english.encode('utf-8'))
        res.append("english_mt : %s" % self.english_mt.encode('utf-8'))
        return "\n".join(res)


def read_lett(f, slang, tlang, source_tokenizer=None, target_tokenizer=None,
              no_html=False, url2source=None, url2target=None,
              detect_english=False):
    s, t = {}, {}
    fh = f
    if f.name.endswith('.gz'):
        fh = gzip.GzipFile(fileobj=fh, mode='r')
    for line in fh:
        lang, mine, enc, url, html, text = line[:-1].split("\t")

        if no_html:
            html = ''
        else:
            html = base64.b64decode(html)

        text = base64.b64decode(text).decode("utf-8")
        # assert lang in [slang, tlang]

        if lang == slang and source_tokenizer is not None:
            text = source_tokenizer.process(text)
        elif lang == tlang and target_tokenizer is not None:
            text = target_tokenizer.process(text)

        p = Page(url, html, text, mine, enc, u"", u"", u"")

        if lang == slang:
            s[url] = p
        elif lang == tlang:
            t[url] = p

    if url2source is not None:
        source_text = defaultdict(list)
        for line in url2source:
            url, text = line.rstrip().split('\t')
            if url in s or url in t:
                source_text[url].append(text.decode('utf-8'))
        for url in source_text:
            text = u'\n'.join(source_text[url])
            if source_tokenizer is not None:
                text = source_tokenizer.process(text)
            if url in s:
                s[url].french = text
            if url in t:
                t[url].french = text

    if url2target is not None:
        target_text = defaultdict(list)
        for line in url2target:
            url, text = line.rstrip().split('\t')
            if url in s or url in t:
                target_text[url].append(text.decode('utf-8'))
        for url in target_text:
            text = u'\n'.join(target_text[url])
            if target_tokenizer is not None:
                text = target_tokenizer.process(text)
            if url in s:
                s[url].english_mt = text
            if url in t:
                t[url].english_mt = text

    if detect_english:
        for url in s:
            s[url].english = get_lang(url, s[url].text, lang='en')
        for url in t:
            t[url].english = get_lang(url, t[url].text, lang='en')

    return s, t


def get_lang(url, text, lang='en'):
    langsplit_output = langsplit(url.decode("utf-8", 'ignore'), text)
    monolingual_text = extract_language(langsplit_output, lang)
    monolingual_text = TextSanitizer.clean_text(monolingual_text)
    return monolingual_text


def langsplit(uri, text,
              langsplit_exec="/home/buck/net/build/mtma_bitext/html_convert/langsplit"):
    cmd = [langsplit_exec, "--printchunks"]
    proc = ExternalTextProcessor(cmd)
    tld = uri.split("/")[0].split(".")[-1]
    header = u"%s tld:%s uri:%s\n" % (magic_number, tld, uri)
    output = proc.process(u"\n".join([header, text]))

    if not output.strip():
        import langid
        res = langid.classify(text)
        lang = res[0]
        header = "%s\tlanguage:%s\tbytes:%d\n" % (header.rstrip(),
                                                  lang,
                                                  len(text.encode("utf-8")))
        return header + text
    return output


def extract_language(langsplit_output, expected_lang):

    text = []
    l = None  # language of current span
    for line in langsplit_output.split("\n"):
        # df6fa1abb58549287111ba8d776733e9 tld:www
        # uri:www.hettahuskies.com/doghotel/hotel.html language:en offset:0
        # bytes: 3853

        if not line.strip():
            continue

        if not line.startswith(magic_number):
            assert l is not None
            if l == expected_lang:
                text.append(line)
        else:
            for kv in line.split():
                if kv.startswith("language:"):
                    l = kv.split(":", 1)[1]

    return u'\n'.join(text)


def write_tokenized_lett(f, pages):
    pass


def corpus_stats(c):
    has_text = 0
    has_english = 0
    has_french = 0
    has_mt = 0
    for url in c:
        if c[url].text:
            has_text += 1
        if c[url].english:
            has_english += 1
        if c[url].french:
            has_french += 1
        if c[url].english_mt:
            has_mt += 1
    return has_text, has_english, has_french, has_mt


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
        'lettfile', help='input lett file', type=argparse.FileType('r'))
    parser.add_argument('-slang', help='source language', default='en')
    parser.add_argument('-tlang', help='target language', default='fr')
    parser.add_argument(
        '-source_tokenizer', help='call to tokenizer, including arguments')
    parser.add_argument(
        '-target_tokenizer', help='call to tokenizer, including arguments')
    parser.add_argument('-url2en', help='url to English text',
                        type=argparse.FileType('r'))
    parser.add_argument('-url2fr', help='url to French text',
                        type=argparse.FileType('r'))
    parser.add_argument('-write', help='filename for pickle file',
                        type=argparse.FileType('wb'))
    args = parser.parse_args()

    source_tokenizer = None
    target_tokenizer = None

    # read source and target corpus
    s, t = read_lett(args.lettfile, args.slang, args.tlang,
                     source_tokenizer, target_tokenizer, False,
                     args.url2fr, args.url2en, True)

    sys.stderr.write("Read %d %s docs and %d %s docs from %s\n" %
                     (len(s), args.slang,
                      len(t), args.tlang, args.lettfile.name))
    sys.stderr.write("Source stats: ")
    has_text, has_english, has_french, has_mt = corpus_stats(s)
    sys.stderr.write("Text: %d\tEnglish:%d\tFrench%d\MT:%d\n"
                     % (has_text, has_english, has_french, has_mt))
    sys.stderr.write("Target stats: ")
    has_text, has_english, has_french, has_mt = corpus_stats(t)
    sys.stderr.write("Text: %d\tEnglish:%d\tFrench%d\MT:%d\n"
                     % (has_text, has_english, has_french, has_mt))
    sys.stderr.write("%d possible pairs for %s\n" %
                     (len(s) * len(t), args.lettfile.name))

    # for url in s:
    #     print s[url]
    #     break
    # for url in t:
    #     print t[url]
    #     break

    if args.write:
        sys.stderr.write("Writing to %s\n" % (args.write.name))
        pickle.dump(s, args.write)
        pickle.dump(t, args.write)

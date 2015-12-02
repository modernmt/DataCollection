import requests
import zlib
import sys
from textsanitzer import TextSanitizer


class CCDownloader(object):

    magic_number = "df6fa1abb58549287111ba8d776733e9"

    def __init__(self):
        self.session = requests.Session()

    # TODO: check if we can deprecate this
    def make_full_path(self, crawl, folder, filename):
        return "https://aws-publicdatasets.s3.amazonaws.com/" +\
               "common-crawl/crawl-data/" + \
               "CC-MAIN-%s" % crawl.replace("_", "-") +\
               "/segments/%d" % (int(folder)) +\
               "/warc/%s" % filename.replace("warc.wat.gz", "warc.gz")

    def _split_record(self, raw_page):
        """ Split common-crawl record into HTML and WARC header """
        empty_lines_seen = 0
        page = raw_page.split("\n")
        for linenr, line in enumerate(page):
            if not line.strip():
                empty_lines_seen += 1
                if empty_lines_seen == 2:
                    return "\n".join(page[linenr + 1:]), \
                           "\n".join(page[:linenr])
        raise ValueError("Input must contain two empty lines")

    def download(self, location, offset, length, html_only=False, timeout=5):
        start_range = offset
        end_range = offset + length - 1
        r = {'Range': "bytes=%d-%d" % (start_range, end_range)}
        try:
            resp = self.session.get(location, headers=r, timeout=timeout)
        except:
            # restart session
            self.session = requests.Session()
            try:
                resp = self.session.get(location, headers=r, timeout=timeout)
            except:
                sys.stderr.write("Error downloading:%s\n" % (str(r)))
                return u""
        try:
            page = zlib.decompress(resp.content, zlib.MAX_WBITS | 16)
        except:
            sys.stderr.write("Error decompressing %d bytes from %s: %d-%d\n"
                             % (len(resp.content),
                                location, start_range, end_range))
            return u''
        page, header = self._split_record(page)
        page = TextSanitizer.to_unicode(page)
        if html_only:
            return page
        return u"%s\n\n%s" % (header.strip(), page)

    # TODO: check if we can deprecate this
    def download_and_write(self, line, outfile, crawl, html_only=False):
        folder, filename = line[4].split('/')
        full_filename = self.make_full_path(crawl, folder, filename)
        offset = int(line[5])
        length = int(line[6])
        raw_page = self.download(full_filename, offset, length)
        sys.stderr.write("%s : %d bytes\n" % (line[1], len(raw_page)))
        if raw_page:
            outfile.write("%s\t%s\n" %
                          (CCDownloader.magic_number, "\t".join(line)))
            if html_only:
                outfile.write(self.extract_html(raw_page))
            else:
                outfile.write(raw_page)

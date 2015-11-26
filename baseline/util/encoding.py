from bs4 import UnicodeDammit

"""
Util to convert everything to Unicode
"""


def to_unicode(data, is_html=False, detwingle=False):
    " converts everything to unicode"
    dammit = UnicodeDammit(data, is_html=is_html)
    if detwingle and dammit.original_encoding == 'windows-1252':
        new_data = UnicodeDammit.detwingle(data)
        dammit = UnicodeDammit(new_data, is_html=is_html)
    return dammit.unicode_markup

if __name__ == "__main__":
    import sys
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-infile', type=argparse.FileType('w'),
                        help='output file', default=sys.stdin)
    parser.add_argument('-outfile', type=argparse.FileType('w'),
                        help='output file', default=sys.stdout)
    parser.add_argument('-html', action='store_true',
                        help='input is HTLM')
    parser.add_argument('-detwingle', action='store_true',
                        help='fix mixed UTF-8 and windows-1252 encodings')
    args = parser.parse_args()

    data = args.infile.read()
    unicode_data = to_unicode(
        data, is_html=args.html, detwingle=args.detwingle)
    args.output.write(unicode_data.encode('utf-8'))

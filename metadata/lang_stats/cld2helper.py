#!/usr/bin/env python
# -*- coding: utf-8 -*-


def read_cld2_languages(infile):
    # Example input:
    # "  TG_UNKNOWN_LANGUAGE          = 25,  // xxx"
    name2code = {}
    code2name = {}
    for line in infile:
        if not line.strip():
            continue
        line = line.strip().split()
        name = line[0]
        code = line[-1]
        if code == "//":
            continue

        assert code not in code2name
        code2name[code] = name
        assert name not in name2code
        name2code[name] = code
    return name2code, code2name


if __name__ == "__main__":
    import argparse
    import sys

    parser = argparse.ArgumentParser()
    parser.add_argument('infile', nargs='?', type=argparse.FileType('r'),
                        default=sys.stdin)
    args = parser.parse_args()

    name2code, code2name = read_cld2_languages(args.infile)
    print name2code
    print code2name

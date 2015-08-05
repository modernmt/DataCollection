#!/usr/bin/python

import sys

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('mapping', help='mapping from filename to url',
                        type=argparse.FileType('r'))
    args = parser.parse_args(sys.argv[1:])

    mapping = {}
    for line in args.mapping:
        filename, url = line.strip().split()
        assert filename not in mapping, "Repeated value: %s\n" % line
        mapping[filename] = url

    for line in sys.stdin:
        filesource, filetarget = line.strip().split()
        if filesource in mapping:
            if filetarget in mapping:
                print mapping[filesource] + "\t" + mapping[filetarget]
            else:
                sys.stderr.write(
                    "Target file mapping not found:" + filetarget + "\n")
        else:
            sys.stderr.write(
                "Source file mapping not found:" + filesource + "\n")

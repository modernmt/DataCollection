#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import base64

for line in sys.stdin:
    s_url, t_url, source, target = line.split("\t")
    source = base64.b64decode(source).decode("utf-8")
    target = base64.b64decode(target).decode("utf-8")
    sys.stdout.write("\t".join([s_url,
                                t_url,
                                repr(source.encode("utf-8")),
                                repr(target.encode("utf-8"))]))
    sys.stdout.write("\n")

#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Reads downloaded website from tar file and writes lett format to be
processed by bitextor pipeline
"""

import sys
import json

for line in sys.stdin:
    domain, data = line.split(" ", 1)
    data = json.loads(data)
    data.pop("links")
    print domain, json.dumps(data)

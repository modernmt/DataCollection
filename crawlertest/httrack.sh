#!/usr/bin/env bash

if [ $# != 3 ]; then
    echo "Usage: $0 start-url output-directory"
    echo "* start-url: initial seed url"
    echo "* output-directory: write logs and downloads to this dir"
    exit
fi

httrack \
--connection-per-second=20 \
--sockets=10 \
--keep-alive \
--disable-security-limits \
--max-rate=500000 \
--display \
--verbose \
--advanced-progressinfo \
--continue \
--robots=0 \
--urlhack \
--index=0 \
-m \
-F 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.80 Safari/537.36' \
-#L500000000 \
--skeleton \
--path=$2 \
$1

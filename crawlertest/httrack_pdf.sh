#!/usr/bin/env bash

if [ $# != 3 ]; then
    echo "Usage: $0 start-url domain output-directory"
    echo "* start-url: initial seed url"
    echo "* domain: stay within this (sub-)domain"
    echo "* output-directory: write logs and downloads to this dir"
    exit
fi

nice httrack \
--connection-per-second=20 \
--sockets=20 \
--keep-alive \
--display \
--verbose \
--advanced-progressinfo \
--disable-security-limits \
--max-rate=10000000 \
--continue \
--robots=0 \
--urlhack \
--index=0 \
--timeout=2 \
--retries=3 \
--extended-parsing yes \
-m \
-F 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.80 Safari/537.36' \
-#L500000000 \
-'*' \
+"*$2/*.html" +"*$2/*.htm" \
+"*$2/*.pdf" \
+"*$2/*/" \
+"*$2/*.php" +"*$2/*.cgi" +"*$2/*.asp" \
-'mime:*/*' +'mime:text/html' +'mime:application/pdf' +'mime:application/x-pdf' \
--path=$3 \
$1

# -'*.jpg' -'*.jpeg' -'*.gif' -'*.ps' -'*.js' -'*.png' -'*.zip' -'*.swf' \
# -'*.flv' -'*.avi' -'*.tgz' -'*.css' -'*.doc' -'*.exe' -'*.mid' -'*.midi' \
# -'*.mp3' -'*.mp4' -'*.mpg'  -'*.mpeg' -'*.mov' -'*.qt' -'*.ram' -'*.rar' \
# -'*.tif' -'*.tiff' -'*.eps' -'*.svg' -'*.txt' -'*.wav' -'*.apk' -'*.torrent' \
# -'*.dll' -'*.msi' -'*.xls' -'*.djvu' -'*.json' -'*.ogv' -'*.ogg' \

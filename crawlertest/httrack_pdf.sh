#!/usr/bin/env bash

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
-'*' +'*.inf.ed.ac.uk/*' \
-'*.jpg' -'*.jpeg' -'*.gif' -'*.ps' -'*.js' -'*.png' -'*.zip' -'*.swf' \
-'*.flv' -'*.avi' -'*.tgz' -'*.css' -'*.doc' -'*.exe' -'*.mid' -'*.midi' \
-'*.mp3' -'*.mp4' -'*.mpg'  -'*.mpeg' -'*.mov' -'*.qt' -'*.ram' -'*.rar' \
-'*.tif' -'*.tiff' -'*.eps' -'*.svg' -'*.txt' -'*.wav' -'*.apk' -'*.torrent' \
-'*.dll' -'*.msi' -'*.xls' -'*.djvu' -'*.json' \
-'mime:*/*' +'mime:text/html' +'mime:application/pdf' +'mime:application/x-pdf' \
--path=$2 \
$1

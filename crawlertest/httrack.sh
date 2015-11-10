httrack \
--connection-per-second=20 \
--sockets=20 \
--keep-alive \
--display \
--verbose \
--advanced-progressinfo \
--disable-security-limits \
--continue \
--robots=0 \
--urlhack \
-m \
-F 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2490.80 Safari/537.36' \
-#L500000000 \
--skeleton \
$1

set -v
python res/zip.py -s 1 -o nanocli src/* src/*/*
echo '#!/usr/bin/env python3' | cat - nanocli.zip > nanocli
rm nanocli.zip
chmod 755 nanocli

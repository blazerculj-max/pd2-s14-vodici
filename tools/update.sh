#!/bin/sh
# Osveži vse podatke in ponovno zgradi stran v docs/.
set -e
cd "$(dirname "$0")/.."
python3 -I tools/fetch_hiim.py --force
python3 -I tools/fetch_wiki.py
python3 -I tools/fetch_pd2tools.py
python3 -I tools/fetch_pd2tools.py --respec
python3 -I tools/build_data.py
python3 -I tools/fetch_images.py
python3 -I tools/build_data.py
python3 -I tools/build_site.py

#!/usr/bin/env bash
# Reproduce the entire Detroit crime & weather project from scratch.
set -euo pipefail
cd "$(dirname "$0")"
python3 00_fetch_data.py
python3 01_build_datasets.py
python3 02_make_figures.py
python3 build_report.py
python3 build_interactive.py
python3 build_index.py
echo "All done — open index.html"

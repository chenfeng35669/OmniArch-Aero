#!/bin/bash
# Read the AirfRANS vtu files into data/airfrans/processed (CPU, ~16 cores, ~10 min).
# Download Dataset.zip from https://airfrans.readthedocs.io and unpack it to data/airfrans/raw/Dataset.
set -euo pipefail
python data/airfrans/prepare.py --raw_dir data/airfrans/raw/Dataset --out_dir data/airfrans/processed --workers 16

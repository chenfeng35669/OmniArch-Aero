#!/bin/bash
# Node features and k-d blocks for the blade into data/blade/processed (CPU, ~5 min).
# Input: data/blade/extracted, written by data/blade/extract_cfx.py from the CFX .res files.
set -euo pipefail
python data/blade/prepare.py --src_dir data/blade/extracted --out_dir data/blade/processed

#!/bin/bash
# Train on AirfRANS (1 GPU, ~1.4 h on an RTX 5090).
#   bash scripts/train_airfrans.sh 0              # similarity specialisation, seed 0
#   bash scripts/train_airfrans.sh 0 airfrans_raw # plain OmniArch arm
set -euo pipefail
SEED=${1:-0}
CONFIG=${2:-airfrans}
python train.py config/$CONFIG.py --seed=$SEED --out_dir=out/${CONFIG}_s$SEED

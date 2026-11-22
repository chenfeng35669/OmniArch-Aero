#!/bin/bash
# Train on the blade (1 GPU, ~1.7 h on an RTX 5090). The reported model averages seeds 0-4.
#   bash scripts/train_blade.sh 0
set -euo pipefail
SEED=${1:-0}
python train.py config/blade.py --seed=$SEED --out_dir=out/blade_s$SEED

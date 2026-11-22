#!/bin/bash
# Predict the 496 test cases with each seed (1 GPU, ~5 min per seed), then score them with the
# official AirfRANS post-processing (CPU, ~10 min).
#   bash scripts/eval_airfrans.sh airfrans 0 1 2
set -euo pipefail
CONFIG=${1:-airfrans}
shift || true
SEEDS=${@:-0 1 2}
CKPTS=$(for s in $SEEDS; do echo out/${CONFIG}_s$s/ckpt.pt; done)
python predict.py --ckpt $CKPTS --split test --out_dir out/${CONFIG}_test
python evaluate.py --pred_dir out/${CONFIG}_test --raw_dir data/airfrans/raw/Dataset --workers 16

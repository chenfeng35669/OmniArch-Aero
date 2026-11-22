#!/bin/bash
# Predict 1200 K and 1616 K with the mean of seeds 0-4 (1 GPU, ~1 min), then score them
# together with the two model-free references (CPU).
#   bash scripts/eval_blade.sh 0 1 2 3 4
set -euo pipefail
SEEDS=${@:-0 1 2 3 4}
CKPTS=$(for s in $SEEDS; do echo out/blade_s$s/ckpt.pt; done)
python predict.py --ckpt $CKPTS --cases e3-model-1200K_001,e3-1616K_001 --out_dir out/blade_test
python evaluate.py --pred_dir out/blade_test

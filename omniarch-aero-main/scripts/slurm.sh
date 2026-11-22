#!/bin/bash
# Submit any script in this folder as a Slurm job from the repository root.
#   bash scripts/slurm.sh gpu scripts/train_airfrans.sh 0
#   bash scripts/slurm.sh cpu scripts/prepare_airfrans.sh
# PYTHON, PARTITION_GPU / PARTITION_CPU and SBATCH_ARGS (e.g. --dependency=afterok:123)
# can be set in the environment. Prints the job id.
set -euo pipefail
KIND=$1; shift
SCRIPT=$1
mkdir -p out/logs
if [ "$KIND" = gpu ]; then
  RES="-p ${PARTITION_GPU:-gpu,lite} --gres=gpu:1 -c 8 --mem 48G -t 12:00:00"
else
  RES="-p ${PARTITION_CPU:-main} -c 16 --mem 96G -t 04:00:00"
fi
sbatch --parsable $RES ${SBATCH_ARGS:-} -J aero-$(basename $SCRIPT .sh) -o out/logs/%x-%j.out \
  --wrap "export PATH=$(dirname ${PYTHON:-$(which python)}):\$PATH; cd $(pwd); bash $*"

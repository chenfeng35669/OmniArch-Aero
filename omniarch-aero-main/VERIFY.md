# Verification against the original experiments

The numbers in the README were produced by the original experiment scripts. This file records
how this rewrite was checked against them (November 2026, scal cluster, RTX 5090).

## 1. Data preparation is bit-identical

`data/airfrans/prepare.py` was run on the AirfRANS Dataset and compared with the original cache:

| item | result |
|---|---|
| mesh, U, p, nu_t, wall mask, aerofoil-to-wall map, normals, wall distance | identical |
| train / test split (504 / 496) | identical |
| k-d blocks (6 cases checked, train and test) | identical |
| official output normalisation (coef_norm) | identical |
| normalisation statistics | max relative difference 1.2e-7 |

`data/blade/prepare.py`: node features identical (max abs difference 0). Blocks are the same
partition (in a different order); the 32 points drawn per block differ because the random
stream differs from the original script.

## 2. Original checkpoints give the original numbers with the new code

The original weights load into `model.AeroNet` without renaming (the blade model's unused
confidence head is dropped). Test fields were predicted with `predict.py` and scored with
`evaluate.py`.

AirfRANS, C_L relative L2 on the 496 test cases:

| | seed 0 | seed 1 | seed 2 | mean +- std |
|---|---|---|---|---|
| original report, similarity | 0.018535 | 0.014860 | 0.021215 | 0.0182 +- 0.0026 |
| this code, similarity | 0.0185 | 0.0149 | 0.0212 | 0.0182 +- 0.0026 |
| original report, dimensional | | | | 0.0514 +- 0.0038 |
| this code, dimensional | 0.0463 | 0.0526 | 0.0553 | 0.0514 +- 0.0038 |

Blade, solid MAE (K), node-wise mean of seeds 0-4 and per seed at 1616 K:

| | 1200 K | 1616 K | 1616 K per seed |
|---|---|---|---|
| original report | 1.5558 | 4.9035 | 5.2546, 4.6772, 4.8617, 4.9311, 4.8143 |
| this code | 1.5558 | 4.9035 | 5.25, 4.68, 4.86, 4.93, 4.81 |
| theta prior alone | 1.84 | 5.34 | |
| similarity conversion | 5.32 | 20.96 | |

## 3. Training from scratch with this code (seed 0)

Early losses match the original logs: AirfRANS epoch 1 / 2 mean loss 1.011 / 0.622 (original
0.998 / 0.622); blade first-step loss 0.9376 (original 0.9371).

Full runs with `scripts/train_*.sh 0`, scored with `scripts/eval_*.sh`:

| | this code, seed 0 | original seeds |
|---|---|---|
| AirfRANS, C_L relative L2 | 0.0174 (rho_L 0.9997) | 0.0149 to 0.0212 |
| blade 1616 K, solid MAE | 4.99 K | 4.68 to 5.25 K |
| blade 1200 K, solid MAE | 1.60 K | 1.45 to 1.78 K |
| training time, one RTX 5090 | AirfRANS 5009 s, blade 6068 s | 9580 s, 6000 s |

Both runs fall inside the spread of the original seeds.

## Known differences from the original scripts

- AirfRANS training now runs the encoder under bf16 autocast as well (the original kept it in
  fp32 during training, bf16 at inference). Training is about twice as fast per step.
- The blade schedule is step-based (69,000 steps) instead of a 6,000 s wall-clock budget.
- Model selection on a validation split is optional (`val_split`); the reported configurations
  train on the full training split for a fixed number of steps, as the originals did.

## Finding: the blade model does not use its encoder

With the original blade checkpoints, replacing the block tokens by noise, zeroing them, or
halving the condition parameters changes the output by less than 1e-8, against an output
scale of 1e-3; the decoder puts 0.15% of its attention on the prefix tokens. All blade cases
share one mesh, so the block tokens are identical across cases, and the case is already
identified by the theta_lin query feature. The blade model therefore acts as a point-wise
correction of theta_lin, and its gain over the prior alone cannot be attributed to the
OmniArch trunk. The AirfRANS model does use its encoder: swapping in the block tokens of
another aerofoil changes the outputs by 0.24 on a scale of 0.72 (normalised units).

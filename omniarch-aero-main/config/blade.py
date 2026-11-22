# OmniArch-Aero on the cooled turbine blade, inlet temperature extrapolation.
# Train on 600/800/1000 K model conditions plus two auxiliary cases, test on 1200 K and 1616 K.
# Reported (mean prediction of seeds 0-4): 1616 K solid MAE 4.90 K, 1200 K 1.56 K.
task = "blade"
data_dir = "data/blade/processed"
out_dir = "out/blade"

train_cases = ["e3-model-600K_001", "e3-model-800K_001", "e3-model-1000K_001",
               "e3-unmodel-600K_001", "e3_redown40_001"]
prior_cases = ["e3-model-600K_001", "e3-model-800K_001", "e3-model-1000K_001"]
batch_size = 49152

gradient_accumulation_steps = 1
max_iters = 69000           # the original runs trained for 6000 s, about 69k steps on one RTX 5090
warmup_iters = 300
learning_rate = 1e-3
min_lr = 5e-5
weight_decay = 0.01
log_interval = 500
ckpt_interval = 10000

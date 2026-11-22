# OmniArch-Aero on AirfRANS, Reynolds extrapolation, similarity specialisation.
# Reported: test C_L relative L2 0.0182 +- 0.0026 over seeds 0, 1, 2 (496 cases).
# 504 training cases x 300 epochs, 4 cases per step -> 37800 steps (~1.4 h on one RTX 5090).
task = "airfrans"
data_dir = "data/airfrans/processed"
out_dir = "out/airfrans"

similarity = True
surf_weight = 5.0
p_weight = 2.0
n_vol_query = 8000
train_split = "train"

gradient_accumulation_steps = 4
max_iters = 37800
warmup_iters = 756
learning_rate = 3e-4
min_lr = 1.5e-5
weight_decay = 0.05
log_interval = 126          # one epoch
ckpt_interval = 6300

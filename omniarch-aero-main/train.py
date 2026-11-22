"""
Train OmniArch-Aero on one task (single GPU).

    python train.py config/airfrans.py
    python train.py config/blade.py --seed=1 --out_dir=out/blade_s1

Each step accumulates gradient_accumulation_steps micro-batches. A micro-batch is one case
from the task: the case's block tokens are encoded and a set of query points is decoded,
and the loss is the mean squared error in normalised output space (optionally weighted
per point and per output field).
"""

import json
import math
import os
import time
from dataclasses import asdict

import numpy as np
import torch

from model import AeroConfig, AeroNet, load_omniarch
from tasks import get_task

# -----------------------------------------------------------------------------
# default config values (see config/*.py)
# I/O
out_dir = "out"
log_interval = 50
eval_interval = 0           # 0: no validation during training
ckpt_interval = 5000
# task
task = "airfrans"
data_dir = "data/airfrans/processed"
# airfrans
similarity = True           # similarity specialisation of inputs and outputs
surf_weight = 1.0           # loss weight of wall points
p_weight = 1.0              # loss weight of the pressure output
n_vol_query = 8000          # random volume points per case and step (plus all wall points)
train_split = "train"
val_split = ""              # e.g. "pseudo_val" to select configurations
# blade
train_cases = []
prior_cases = []
batch_size = 49152          # query nodes per step
# model
init_from = "omniarch"      # "omniarch": trunk from OmniArch-base, "scratch": random
omniarch_ckpt = "weights/omniarch-base.pt"
n_layer = 8
n_head = 16
n_embd = 1024
ffn = 2816
n_dec_layer = 1
dec_ffn = 1408
# optimiser
learning_rate = 3e-4
max_iters = 37800
warmup_iters = 756
min_lr = 1.5e-5
weight_decay = 0.05
beta1 = 0.9
beta2 = 0.95
grad_clip = 1.0
gradient_accumulation_steps = 4
# system
seed = 0
device = "cuda"
# -----------------------------------------------------------------------------
config_keys = [k for k, v in globals().items() if not k.startswith("_") and isinstance(v, (int, float, bool, str, list))]
exec(open("configurator.py").read())
config = {k: globals()[k] for k in config_keys}
TASK_KEYS = dict(airfrans=["similarity", "surf_weight", "p_weight", "n_vol_query", "train_split", "val_split"],
                 blade=["train_cases", "prior_cases", "batch_size"])
# -----------------------------------------------------------------------------

os.makedirs(out_dir, exist_ok=True)
torch.manual_seed(seed)
np.random.seed(seed)

task_args = {k: config[k] for k in TASK_KEYS[task]}
T = get_task(task, data_dir=data_dir, device=device, seed=seed, **task_args)

model_args = dict(n_layer=n_layer, n_head=n_head, n_embd=n_embd, ffn=ffn, n_dec_layer=n_dec_layer, dec_ffn=dec_ffn)
model_args.update(T.model_args)
model = AeroNet(AeroConfig(**model_args))
if init_from == "omniarch":
    load_omniarch(model, omniarch_ckpt)
print(f"model: {model.num_params() / 1e6:.1f}M parameters")
model.to(device)

optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate, betas=(beta1, beta2), weight_decay=weight_decay)


def get_lr(it):
    """Linear warmup, then cosine decay to min_lr at max_iters."""
    if it < warmup_iters:
        return learning_rate * (it + 1) / warmup_iters
    ratio = (it - warmup_iters) / max(1, max_iters - warmup_iters)
    return min_lr + 0.5 * (1.0 + math.cos(math.pi * ratio)) * (learning_rate - min_lr)


def loss_fn(batch):
    with torch.autocast(device_type="cuda", dtype=torch.bfloat16):
        pred = model(*batch["inputs"], batch["xq"])
    err = (pred.float() - batch["y"]) ** 2
    if batch["col_w"] is not None:
        err = err * batch["col_w"]
    err = err.mean(-1)
    w = batch["w"]
    return err.mean() if w is None else (err * w).sum() / w.sum()


def save(it):
    ckpt = dict(model=model.state_dict(), model_args=asdict(model.config), task=task, task_args=task_args,
                task_state=T.state(), iter_num=it, config=config)
    torch.save(ckpt, os.path.join(out_dir, "ckpt.pt"))


log = open(os.path.join(out_dir, "log.jsonl"), "a")
t0 = time.time()
loss_acc = 0.0
for it in range(max_iters):
    lr = get_lr(it)
    for group in optimizer.param_groups:
        group["lr"] = lr
    optimizer.zero_grad(set_to_none=True)
    for _ in range(gradient_accumulation_steps):
        loss = loss_fn(T.get_batch())
        (loss / gradient_accumulation_steps).backward()
        loss_acc += loss.item() / gradient_accumulation_steps
    if grad_clip > 0:
        torch.nn.utils.clip_grad_norm_(model.parameters(), grad_clip)
    optimizer.step()

    if (it + 1) % log_interval == 0 or it == 0:
        n = 1 if it == 0 else log_interval
        rec = dict(iter=it + 1, loss=loss_acc / n, lr=lr, time_s=round(time.time() - t0, 1))
        loss_acc = 0.0
        if eval_interval and (it + 1) % eval_interval == 0:
            model.eval()
            rec.update(T.evaluate(model))
            model.train()
        print(" ".join(f"{k} {v:.4g}" if isinstance(v, float) else f"{k} {v}" for k, v in rec.items()), flush=True)
        log.write(json.dumps(rec) + "\n")
        log.flush()
    if (it + 1) % ckpt_interval == 0:
        save(it + 1)

save(max_iters)
print(f"done: {max_iters} iters in {time.time() - t0:.0f}s, checkpoint {out_dir}/ckpt.pt")

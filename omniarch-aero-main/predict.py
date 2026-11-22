"""
Full-field prediction with one or more checkpoints. With several checkpoints (seeds) the
saved field is their node-wise mean; each checkpoint's own field is saved as well.

    python predict.py --ckpt out/airfrans/ckpt.pt --split test --out_dir out/airfrans/pred_test
    python predict.py --ckpt out/blade_s*/ckpt.pt --cases e3-model-1200K_001,e3-1616K_001 --out_dir out/blade/pred

Writes <out_dir>/<case>.npz (fields in physical units), <out_dir>/<seed i>/<case>.npz when
there are several checkpoints, and <out_dir>/index.json for evaluate.py. Test truth is not read.
"""

import argparse
import json
import os
import time

import numpy as np
import torch

from model import AeroConfig, AeroNet
from tasks import get_task

ap = argparse.ArgumentParser()
ap.add_argument("--ckpt", nargs="+", required=True)
ap.add_argument("--out_dir", required=True)
ap.add_argument("--split", default="", help="airfrans: a split name in splits.json")
ap.add_argument("--cases", default="", help="comma-separated case names")
ap.add_argument("--data_dir", default="", help="default: the data_dir the checkpoint was trained on")
args = ap.parse_args()

device = "cuda"
models, ck = [], None
for path in args.ckpt:
    ck = torch.load(path, map_location="cpu", weights_only=False)
    m = AeroNet(AeroConfig(**ck["model_args"]))
    m.load_state_dict(ck["model"])
    models.append(m.to(device).eval())
data_dir = args.data_dir or ck["config"]["data_dir"]
T = get_task(ck["task"], data_dir=data_dir, device=device, state=ck["task_state"], train=False, **ck["task_args"])
cases = args.cases.split(",") if args.cases else T.splits[args.split]
os.makedirs(args.out_dir, exist_ok=True)

seconds = []
for i, name in enumerate(cases):
    preds = []
    for k, m in enumerate(models):
        torch.cuda.synchronize()
        t0 = time.time()
        preds.append(T.predict_case(m, name))
        torch.cuda.synchronize()
        seconds.append(time.time() - t0)
        if len(models) > 1:
            os.makedirs(os.path.join(args.out_dir, f"seed{k}"), exist_ok=True)
            np.savez(os.path.join(args.out_dir, f"seed{k}", name + ".npz"), **preds[-1])
    mean = {f: np.mean([p[f] for p in preds], axis=0).astype(np.float32) for f in preds[0]}
    np.savez(os.path.join(args.out_dir, name + ".npz"), **mean)
    if (i + 1) % 50 == 0 or i + 1 == len(cases):
        print(f"{i + 1}/{len(cases)} cases, {np.median(seconds):.2f}s per case and checkpoint", flush=True)

index = dict(task=ck["task"], data_dir=os.path.abspath(data_dir), task_args=ck["task_args"],
             task_state=ck["task_state"], ckpts=[os.path.abspath(p) for p in args.ckpt], cases=cases,
             n_models=len(models), median_seconds=float(np.median(seconds)))
with open(os.path.join(args.out_dir, "index.json"), "w") as f:
    json.dump(index, f, indent=1)

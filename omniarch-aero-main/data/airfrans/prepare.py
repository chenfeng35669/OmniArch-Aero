"""
Read the AirfRANS dataset (vtu / vtp, https://airfrans.readthedocs.io) once and write one npz
per case with the mesh, the fields, the aerofoil arrays used for lift and drag, and the
k-d blocks. Then write the splits and the normalisation constants.

    python data/airfrans/prepare.py --raw_dir data/airfrans/raw/Dataset --out_dir data/airfrans/processed

Needs pyvista. About 2 minutes with 16 workers for the 1000 Reynolds-task cases.
"""

import argparse
import json
import os
import sys
from multiprocessing import Pool

import numpy as np
import torch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from tasks import kd_blocks  # noqa: E402
from tasks.airfrans import NU, param_values, query_features, targets, token_features  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--raw_dir", default="data/airfrans/raw/Dataset")
ap.add_argument("--out_dir", default="data/airfrans/processed")
ap.add_argument("--n_blocks", type=int, default=2048)
ap.add_argument("--workers", type=int, default=16)
args = ap.parse_args()


def read_case(name):
    """Arrays as in the official AirfRANS Dataset (sample=None), plus blocks."""
    import pyvista as pv
    internal = pv.read(os.path.join(args.raw_dir, name, name + "_internal.vtu"))
    aerofoil = pv.read(os.path.join(args.raw_dir, name, name + "_aerofoil.vtp"))
    U = np.asarray(internal.point_data["U"])
    surf = U[:, 0] == 0  # official wall mask
    pos = np.asarray(internal.points)[:, :2].astype(np.float32)
    # map each aerofoil point to its wall point (exact coordinate match, as the official reorganize)
    wall = np.asarray(internal.points)[surf, :2]
    lookup = {}
    for i, p in enumerate(wall):
        lookup.setdefault((float(p[0]), float(p[1])), i)
    af_to_wall = np.array([lookup[(float(p[0]), float(p[1]))] for p in np.asarray(aerofoil.points)[:, :2]], np.int64)
    af_normals = np.asarray(aerofoil.point_data["Normals"]).astype(np.float32)
    normal = np.zeros((len(pos), 2), np.float32)
    nw = np.zeros((surf.sum(), 2), np.float32)
    nw[af_to_wall] = -af_normals[:, :2]
    normal[surf] = nw
    sdf = (-np.asarray(internal.point_data["implicit_distance"])).astype(np.float32)
    Uinf, alpha = float(name.split("_")[2]), float(name.split("_")[3])
    block_id, block_centers = kd_blocks(pos, args.n_blocks)
    conn = np.asarray(aerofoil.lines).reshape(-1, 3)[:, 1:].astype(np.int32)
    np.savez(os.path.join(args.out_dir, "cases", name + ".npz"),
             pos=pos, U=U[:, :2].astype(np.float32), p=np.asarray(internal.point_data["p"]).astype(np.float32),
             nut=np.asarray(internal.point_data["nut"]).astype(np.float32), wd=np.maximum(sdf, 0),
             normal=normal, surf=surf, af_normals=af_normals,
             af_length=np.asarray(aerofoil.cell_data["Length"]).astype(np.float32), af_conn=conn,
             af_to_wall=af_to_wall, Uinf=Uinf, alpha=alpha, Re=Uinf / NU,
             block_id=block_id, block_centers=block_centers)
    return name


def load(name):
    z = np.load(os.path.join(args.out_dir, "cases", name + ".npz"))
    c = {k: torch.from_numpy(np.asarray(z[k])) for k in ("pos", "wd", "surf")}
    c["nrm"] = torch.from_numpy(z["normal"])
    c["y"] = torch.from_numpy(np.concatenate([z["U"], z["p"][:, None], z["nut"][:, None]], 1))
    c.update(Uinf=float(z["Uinf"]), alpha=float(z["alpha"]), Re=float(z["Re"]))
    return c


if __name__ == "__main__":
    os.makedirs(os.path.join(args.out_dir, "cases"), exist_ok=True)
    with open(os.path.join(args.raw_dir, "manifest.json")) as f:
        manifest = json.load(f)
    train, test = manifest["reynolds_train"], manifest["reynolds_test"]
    with Pool(args.workers) as pool:
        for i, _ in enumerate(pool.imap_unordered(read_case, train + test, chunksize=4)):
            if (i + 1) % 100 == 0:
                print(f"read {i + 1}/{len(train) + len(test)} cases", flush=True)

    # splits: official train / test, and a pseudo-extrapolation split of train for model selection
    Re = {n: float(n.split("_")[2]) / NU for n in train}
    splits = dict(train=train, test=test,
                  pseudo_train=[n for n in train if 3.3e6 < Re[n] < 4.7e6],
                  pseudo_val=[n for n in train if not 3.3e6 < Re[n] < 4.7e6])
    with open(os.path.join(args.out_dir, "splits.json"), "w") as f:
        json.dump(splits, f, indent=1)
    print({k: len(v) for k, v in splits.items()})

    # normalisation constants over the train split (float64 sums of float32 features)
    cases = [load(n) for n in train]
    lo = np.min([c["pos"].numpy().min(0) for c in cases], 0).astype(np.float64)
    hi = np.max([c["pos"].numpy().max(0) for c in cases], 0).astype(np.float64)
    ident = lambda d: dict(mean=[0.0] * d, std=[1.0] * d)  # noqa: E731
    raw_st = dict(bbox_lo=lo.tolist(), bbox_hi=hi.tolist())
    for key, d in (("token", 6), ("sim_q", 8), ("raw_q", 7), ("sim_y", 4), ("raw_y", 4)):
        raw_st[key + "_mean"], raw_st[key + "_std"] = ident(d)["mean"], ident(d)["std"]
    feats = dict(token=lambda c: token_features(c, raw_st),
                 sim_q=lambda c: query_features(c, slice(None), True, raw_st),
                 raw_q=lambda c: query_features(c, slice(None), False, raw_st),
                 sim_y=lambda c: targets(c["y"], c, True, raw_st),
                 raw_y=lambda c: targets(c["y"], c, False, raw_st))
    stats = dict(bbox_lo=raw_st["bbox_lo"], bbox_hi=raw_st["bbox_hi"])
    for key, fn in feats.items():
        s = ss = 0.0
        n = 0
        for c in cases:
            x = fn(c).double()
            s, ss, n = s + x.sum(0), ss + (x * x).sum(0), n + len(x)
        mean = s / n
        stats[key + "_mean"] = mean.float().tolist()
        stats[key + "_std"] = torch.sqrt(torch.clamp(ss / n - mean ** 2, min=1e-12)).float().tolist()
    for key, sim in (("sim_p", True), ("raw_p", False)):
        p = np.stack([param_values(c["Re"], c["alpha"], c["Uinf"], sim) for c in cases]).astype(np.float64)
        stats[key + "_mean"] = p.mean(0).astype(np.float32).tolist()
        stats[key + "_std"] = np.maximum(p.std(0), 1e-12).astype(np.float32).tolist()
    with open(os.path.join(args.out_dir, "stats.json"), "w") as f:
        json.dump(stats, f, indent=1)

    # official output normalisation (AirfRANS / Transolver: first 90% of reynolds_train,
    # float64 mean, float32 deviations), used only by the official MSE in evaluate.py
    ys = [c["y"].numpy().astype(np.float64) for c in cases[:len(train) - int(0.1 * len(train))]]
    n = sum(len(y) for y in ys)
    mean = (sum(y.sum(0) for y in ys) / n).astype(np.float32)
    std = np.sqrt(sum(((y.astype(np.float32) - mean) ** 2).sum(0, dtype=np.float64) for y in ys) / n).astype(np.float32)
    with open(os.path.join(args.out_dir, "coef_norm.json"), "w") as f:
        json.dump(dict(mean_out=mean.tolist(), std_out=std.tolist()), f, indent=1)
    print(f"wrote {args.out_dir}")

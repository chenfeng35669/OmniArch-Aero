"""
Build the blade task data from the extracted CFX results (see data/blade/README.md):
    <src_dir>/geometry.npz            solid and fluid node coordinates, fluid wall distance,
                                      gas-side surface nodes
    <src_dir>/case_<case>.npz         solid_T and the condition scalars, one per case
    <src_dir>/conditions.json         similarity numbers per case

    python data/blade/prepare.py --src_dir data/blade/extracted --out_dir data/blade/processed

Writes
    geometry.npz   feats (N, 6) per solid node: coordinates scaled to [-1, 1], radius scaled
                   to [0, 1], log distance to the nearest fluid node, log distance to the
                   gas-side surface; xyz; outer_nodes; and the block tokens' inputs:
                   block_points (K * P, 6), block_index (K * P,), block_centers (K, 3)
    cases/<case>.npz   T (N,) solid temperature
    cases.json         Tg, Tc (inlet total temperatures, K) and the five similarity numbers
"""

import argparse
import json
import os
import sys

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from tasks import kd_blocks  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--src_dir", default="data/blade/extracted")
ap.add_argument("--out_dir", default="data/blade/processed")
ap.add_argument("--n_blocks", type=int, default=4096)
ap.add_argument("--points_per_block", type=int, default=32)
ap.add_argument("--seed", type=int, default=0)
ap.add_argument("--workers", type=int, default=8)
args = ap.parse_args()

SIM_KEYS = ["mc/mm%", "Tc/Tm", "PR", "n/sqrtT", "m*sqrtT/P"]
os.makedirs(os.path.join(args.out_dir, "cases"), exist_ok=True)

# conditions and solid temperatures
with open(os.path.join(args.src_dir, "conditions.json")) as f:
    cond = json.load(f)["cases"]
cases = {}
for name, c in cond.items():
    z = np.load(os.path.join(args.src_dir, f"case_{name}.npz"))
    np.savez(os.path.join(args.out_dir, "cases", name + ".npz"), T=z["solid_T"].astype(np.float32))
    cases[name] = dict(Tg=float(c["Tg"]), Tc=float(c["Tc"]), sim=[float(c["similarity_params"][k]) for k in SIM_KEYS])
with open(os.path.join(args.out_dir, "cases.json"), "w") as f:
    json.dump(cases, f, indent=1)
print(f"{len(cases)} cases")

# per-node geometric features (shared by all cases)
g = np.load(os.path.join(args.src_dir, "geometry.npz"))
xyz = g["solid_xyz"].astype(np.float32)
outer = g["outer_nodes"].astype(np.int64)
d_fluid = cKDTree(g["fluid_xyz"]).query(xyz, workers=args.workers)[0]
d_outer = cKDTree(xyz[outer]).query(xyz, workers=args.workers)[0]
lo, hi = xyz.min(0), xyz.max(0)
r = g["solid_r"].astype(np.float32)
logd = lambda d: np.log10(np.maximum(d.astype(np.float32), 1e-6) / 1e-6) / 4  # ~[0, 1] for d up to 1 cm  # noqa: E731
feats = np.concatenate([(xyz - (lo + hi) / 2) / ((hi - lo) / 2), ((r - r.min()) / (r.max() - r.min()))[:, None],
                        logd(d_fluid)[:, None], logd(d_outer)[:, None]], 1).astype(np.float32)

# k-d blocks; each block token is built from points_per_block random nodes of the block
block_id, centers = kd_blocks(xyz, args.n_blocks)
order = np.argsort(block_id, kind="stable")
starts = np.concatenate([[0], np.cumsum(np.bincount(block_id, minlength=args.n_blocks))])
rng = np.random.default_rng(args.seed)
P = args.points_per_block
sel = np.stack([rng.choice(order[starts[b]:starts[b + 1]], P, replace=False) for b in range(args.n_blocks)])
np.savez(os.path.join(args.out_dir, "geometry.npz"), feats=feats, xyz=xyz, outer_nodes=outer,
         block_points=feats[sel.ravel()], block_index=np.repeat(np.arange(args.n_blocks), P),
         block_centers=((centers - (lo + hi) / 2) / ((hi - lo) / 2)).astype(np.float32))
print(f"{len(xyz)} solid nodes, {args.n_blocks} blocks of {np.diff(starts).min()}-{np.diff(starts).max()} nodes, "
      f"wrote {args.out_dir}")

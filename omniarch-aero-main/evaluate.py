"""
Score the fields written by predict.py against the truth. This is the only script that reads
test truth.

    python evaluate.py --pred_dir out/airfrans/pred_test --raw_dir data/airfrans/raw/Dataset
    python evaluate.py --pred_dir out/blade/pred

airfrans: official AirfRANS post-processing (lift and drag from the vtu meshes with wall
shear stress), normalised MSE, Spearman correlation; needs the raw dataset (--raw_dir).
blade: solid and gas-side surface temperature errors and the hot spot, together with two
reference methods that need no model: the theta prior alone, and similarity conversion
(theta copied from the nearest prior case).

The ensemble field (<pred_dir>) and each seed (<pred_dir>/seed*) are scored separately;
results go to <pred_dir>/metrics.json.
"""

import argparse
import glob
import json
import os
from multiprocessing import Pool

import numpy as np

from tasks import get_task

ap = argparse.ArgumentParser()
ap.add_argument("--pred_dir", required=True)
ap.add_argument("--raw_dir", default="data/airfrans/raw/Dataset")
ap.add_argument("--workers", type=int, default=8)
args = ap.parse_args()

with open(os.path.join(args.pred_dir, "index.json")) as f:
    index = json.load(f)
cases, data_dir = index["cases"], index["data_dir"]
runs = {"mean": args.pred_dir}
runs.update({os.path.basename(d): d for d in sorted(glob.glob(os.path.join(args.pred_dir, "seed*")))})


def airfrans_case(job):
    from tasks.airfrans import official_case_metrics
    run_dir, name, coef_norm = job
    pred = dict(np.load(os.path.join(run_dir, name + ".npz")))
    return official_case_metrics(args.raw_dir, data_dir, name, pred, coef_norm)


results = {}
if index["task"] == "airfrans":
    from tasks.airfrans import aggregate
    with open(os.path.join(data_dir, "coef_norm.json")) as f:
        coef_norm = json.load(f)
    for run, d in runs.items():
        if run == "mean" and index["n_models"] > 1:
            continue  # AirfRANS results are reported per seed
        with Pool(args.workers) as pool:
            records = pool.map(airfrans_case, [(d, n, coef_norm) for n in cases])
        results[run] = dict(aggregate=aggregate(records), cases=records)
        a = results[run]["aggregate"]
        print(f"{run}: C_L rel L2 {a['C_L_rel_L2']:.4f}  rho_L {a['rho_L']:.4f}  "
              f"vol MSE {a['vol_mse']:.5f}  surf MSE {a['surf_mse']:.5f}  ({a['n_cases']} cases)")
    seeds = [r["aggregate"]["C_L_rel_L2"] for r in results.values()]
    if len(seeds) > 1:
        print(f"C_L rel L2 over {len(seeds)} seeds: {np.mean(seeds):.4f} +- {np.std(seeds):.4f}")

elif index["task"] == "blade":
    from tasks.blade import T_of, temperature_metrics
    T = get_task("blade", data_dir=data_dir, device="cpu", state=index["task_state"], train=False, **index["task_args"])
    xyz, outer = T.geom["xyz"], T.geom["outer_nodes"]
    for name in cases:
        true, c = T.T(name), T.cases[name]
        ref = dict(theta_prior=T_of(T.theta_prior(name).astype(np.float64), c["Tg"], c["Tc"]),
                   similarity_conversion=T_of(T.theta_nearest(name), c["Tg"], c["Tc"]))
        for run, d in list(runs.items()) + [(k, None) for k in ref]:
            pred = np.load(os.path.join(d, name + ".npz"))["T"] if d else ref[run]
            m = temperature_metrics(pred, true, xyz, outer)
            results.setdefault(run, {})[name] = m
            print(f"{name:20s} {run:22s} MAE {m['mae_K']:6.2f} K  surface {m['outer_mae_K']:6.2f} K  "
                  f"Tmax err {m['Tmax_err_K']:+6.1f} K  hot spot {m['hotspot_dist_mm']:.1f} mm")

with open(os.path.join(args.pred_dir, "metrics.json"), "w") as f:
    json.dump(results, f, indent=1)

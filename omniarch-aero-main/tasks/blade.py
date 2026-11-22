"""
Cooled turbine blade (one rotor blade, conjugate heat transfer by CFX): predict the metal
temperature at engine conditions from cases run at lower inlet temperature.

Every case shares one mesh (3,304,055 solid nodes). A case differs by its operating
condition: main inlet total temperature Tg, coolant total temperature Tc, flow rates,
pressure and speed. Train on 600/800/1000 K model conditions plus two auxiliary cases;
test on 1200 K and the 1616 K engine condition.

Similarity specialisation:
  * the target is the dimensionless temperature theta = (Tg - T) / (Tg - Tc);
  * the condition enters only through five similarity numbers (coolant/main mass flow
    ratio, Tc/Tm, pressure ratio, n/sqrt(T), m sqrt(T)/P), scaled by the 600 K values;
  * the residual left by the similarity law (the change of theta with temperature level,
    mostly from temperature-dependent properties) is handled by a prior plus a learned
    correction: theta = theta_lin + d_theta. theta_lin is the node-wise straight-line fit of
    theta against g = Tg / 1000 over the prior cases (600/800/1000 K). The model gets
    theta_lin as a 7th query feature and outputs d_theta, starting from exactly zero.
    For a training case that is itself a prior case, theta_lin is fitted leaving it out.

Data layout written by data/blade/prepare.py:
    <data_dir>/geometry.npz       node features, block points, block centres, outer surface
    <data_dir>/cases/<case>.npz   T (solid temperature), one per case
    <data_dir>/cases.json         Tg, Tc and similarity numbers per case
"""

import json
import os

import numpy as np
import torch


def theta_of(T, Tg, Tc):
    return (Tg - T) / (Tg - Tc)


def T_of(theta, Tg, Tc):
    return Tg - theta * (Tg - Tc)


class BladeTask:

    def __init__(self, data_dir, train_cases=(), prior_cases=(), batch_size=49152, device="cuda", seed=0,
                 state=None, train=True):
        self.data_dir = data_dir
        self.device = device
        self.batch_size = batch_size
        self.rng = np.random.default_rng(seed)
        with open(os.path.join(data_dir, "cases.json")) as f:
            self.cases = json.load(f)
        g = np.load(os.path.join(data_dir, "geometry.npz"))
        self.geom = {k: g[k] for k in g.files}
        self.n = len(self.geom["feats"])
        self.model_args = dict(n_dim=3, point_dim=6, query_dim=7, out_dim=1, n_params=5, param_dim=1,
                               zero_init_head=True)
        t = lambda a: torch.from_numpy(np.ascontiguousarray(a)).to(device)  # noqa: E731
        self.block_inputs = (t(self.geom["block_points"]), t(self.geom["block_index"]).long(),
                             t(self.geom["block_centers"]))
        self.feats = t(self.geom["feats"])
        self._T = {}
        if state is None:
            th = np.concatenate([self.theta_true(c) for c in train_cases])
            state = dict(prior_cases=list(prior_cases), theta_mean=float(th.mean()), theta_std=float(th.std()),
                         param_scale=self.cases[prior_cases[0]]["sim"])
        self.st = state
        self.train_cases = list(train_cases)
        if train:
            self.train_data = []
            for c in self.train_cases:
                fit = [p for p in self.st["prior_cases"] if p != c]
                thl = self.theta_prior(c, fit)
                d_theta = self.theta_true(c) - thl
                print(f"{c}: prior from {fit}, |d_theta| mean {np.abs(d_theta).mean():.5f}")
                self.train_data.append(dict(params=self.params(c), thl=t(self.norm_theta(thl))[:, None],
                                            y=t((d_theta / np.float32(self.st["theta_std"])).astype(np.float32))))
            self.perm, self.pos = None, 0

    def state(self):
        return self.st

    def T(self, case):
        """True solid temperature (only ever read for training and prior cases, and in evaluate.py)."""
        if case not in self._T:
            self._T[case] = np.load(os.path.join(self.data_dir, "cases", case + ".npz"))["T"]
        return self._T[case]

    def theta_true(self, case):
        return theta_of(self.T(case).astype(np.float64), self.cases[case]["Tg"], self.cases[case]["Tc"]).astype(np.float32)

    def params(self, case):
        p = np.array(self.cases[case]["sim"], np.float32) / np.array(self.st["param_scale"], np.float32)
        return torch.from_numpy(p).to(self.device)

    def norm_theta(self, theta):
        return ((theta - np.float32(self.st["theta_mean"])) / np.float32(self.st["theta_std"])).astype(np.float32)

    def theta_prior(self, case, fit_cases=None):
        """theta_lin: node-wise least-squares line of theta against Tg / 1000 over fit_cases."""
        fit_cases = fit_cases or self.st["prior_cases"]
        g = np.array([self.cases[c]["Tg"] / 1000.0 for c in fit_cases])
        thetas = [theta_of(self.T(c).astype(np.float64), self.cases[c]["Tg"], self.cases[c]["Tc"]) for c in fit_cases]
        th_bar = sum(thetas) / len(thetas)
        slope = sum((gi - g.mean()) * (th - th_bar) for gi, th in zip(g, thetas)) / ((g - g.mean()) ** 2).sum()
        return (th_bar + slope * (self.cases[case]["Tg"] / 1000.0 - g.mean())).astype(np.float32)

    def theta_nearest(self, case):
        """Similarity conversion baseline: theta copied from the prior case with the closest Tg."""
        near = min(self.st["prior_cases"], key=lambda c: abs(self.cases[c]["Tg"] - self.cases[case]["Tg"]))
        return theta_of(self.T(near).astype(np.float64), self.cases[near]["Tg"], self.cases[near]["Tc"])

    def get_batch(self):
        """batch_size random solid nodes of one random training case."""
        d = self.train_data[self.rng.integers(len(self.train_data))]
        if self.perm is None or self.pos + self.batch_size > self.n:
            self.perm, self.pos = self.rng.permutation(self.n), 0
        idx = torch.from_numpy(self.perm[self.pos:self.pos + self.batch_size]).to(self.device)
        self.pos += self.batch_size
        return dict(inputs=(*self.block_inputs, d["params"]), xq=torch.cat([self.feats[idx], d["thl"][idx]], 1),
                    y=d["y"][idx, None], w=None, col_w=None)

    @torch.no_grad()
    def predict(self, model, case, chunk=131072):
        """Solid temperature (N,) in K for any case with Tg, Tc and similarity numbers in cases.json."""
        thl = self.theta_prior(case)
        thl_n = torch.from_numpy(self.norm_theta(thl)).to(self.device)[:, None]
        out = np.empty(self.n, np.float32)
        with torch.autocast("cuda", dtype=torch.bfloat16):
            tokens = model.encode(*self.block_inputs, self.params(case))
            for i in range(0, self.n, chunk):
                xq = torch.cat([self.feats[i:i + chunk], thl_n[i:i + chunk]], 1)
                out[i:i + chunk] = model.decode(xq, tokens)[:, 0].float().cpu().numpy()
        theta = thl.astype(np.float64) + out.astype(np.float64) * self.st["theta_std"]
        return T_of(theta, self.cases[case]["Tg"], self.cases[case]["Tc"]).astype(np.float32)

    def predict_case(self, model, name):
        return dict(T=self.predict(model, name))

    def evaluate(self, model):
        return {}


def temperature_metrics(pred, true, xyz, outer_nodes):
    """MAE over all solid nodes and over the gas-side surface, and the hot spot."""
    pred, true = pred.astype(np.float64), true.astype(np.float64)
    err = pred - true
    it, ip = int(np.argmax(true)), int(np.argmax(pred))
    return dict(mae_K=float(np.abs(err).mean()), rmse_K=float(np.sqrt((err ** 2).mean())),
                max_abs_K=float(np.abs(err).max()), bias_K=float(err.mean()),
                outer_mae_K=float(np.abs(err[outer_nodes]).mean()),
                Tmax_true_K=float(true[it]), Tmax_err_K=float(pred[ip] - true[it]),
                hotspot_err_K=float(pred[it] - true[it]),
                hotspot_dist_mm=float(np.linalg.norm(xyz[ip].astype(np.float64) - xyz[it]) * 1000))

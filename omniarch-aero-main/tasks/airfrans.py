"""
AirfRANS (Bonnet et al., NeurIPS 2022 Datasets), Reynolds task: train on Re in [3e6, 5e6],
test on 496 cases with Re outside that range. Inputs per case: a 2-D RANS mesh, the free
stream speed and the angle of attack. Outputs per mesh point: u, v, p (p / rho) and nu_t.

similarity=True is the "similarity specialisation": the model never sees dimensional
inputs or outputs. Wall distance enters as y+ ~ d Re^0.9 and delta ~ d Re^0.2, the
condition as (log10 Re, sin a, cos a), and the outputs are u/U, v/U, Cp and
log10(1 + nu_t / nu). similarity=False feeds raw quantities (the plain OmniArch arm).

Data layout written by data/airfrans/prepare.py:
    <data_dir>/cases/<case>.npz   mesh, fields, aerofoil arrays, k-d blocks
    <data_dir>/splits.json        train / test (official) and pseudo_train / pseudo_val
    <data_dir>/stats.json         normalisation constants over the train split
    <data_dir>/coef_norm.json     official output normalisation (for the official MSE)
"""

import json
import math
import os

import numpy as np
import torch

NU = 1.56e-5      # kinematic viscosity used by AirfRANS, chord = 1 m, Re = U / NU
WD_EPS = 1e-7     # floor for log wall distance
N_PARAMS = 3


# -----------------------------------------------------------------------------
# features (all float32 torch tensors on the case device)

def _norm(x, mean, std):
    return (x - torch.tensor(mean, dtype=x.dtype, device=x.device)) / torch.tensor(std, dtype=x.dtype, device=x.device)


def token_features(c, st):
    """(N, 6): coordinates scaled by the bbox, log10 wall distance, normal, wall flag."""
    lo = torch.tensor(st["bbox_lo"], device=c["pos"].device)
    hi = torch.tensor(st["bbox_hi"], device=c["pos"].device)
    xy = (c["pos"] - (lo + hi) / 2) / torch.clamp((hi - lo) / 2, min=1e-9)
    lwd = torch.log10(torch.clamp(c["wd"], min=WD_EPS))
    f = torch.stack([xy[:, 0], xy[:, 1], lwd, c["nrm"][:, 0], c["nrm"][:, 1], c["surf"].float()], -1)
    return _norm(f, st["token_mean"], st["token_std"])


def query_features(c, idx, similarity, st):
    pos, wd, nrm = c["pos"][idx], c["wd"][idx], c["nrm"][idx]
    a = c["alpha"] * math.pi / 180
    one = torch.ones_like(wd)
    if similarity:  # [x, y, log10(1+y+), log10(1+delta), sin a, cos a, nx, ny]
        q = torch.stack([pos[:, 0], pos[:, 1], torch.log10(1 + wd * c["Re"] ** 0.9),
                         torch.log10(1 + wd * c["Re"] ** 0.2), one * math.sin(a), one * math.cos(a),
                         nrm[:, 0], nrm[:, 1]], -1)
        return _norm(q, st["sim_q_mean"], st["sim_q_std"])
    # [x, y, log10 d, U cos a, U sin a, nx, ny]
    q = torch.stack([pos[:, 0], pos[:, 1], torch.log10(torch.clamp(wd, min=WD_EPS)),
                     one * (c["Uinf"] * math.cos(a)), one * (c["Uinf"] * math.sin(a)), nrm[:, 0], nrm[:, 1]], -1)
    return _norm(q, st["raw_q_mean"], st["raw_q_std"])


def targets(y, c, similarity, st):
    """Physical (Q, 4) u, v, p, nu_t -> normalised model outputs."""
    if similarity:
        U = c["Uinf"]
        y = torch.stack([y[:, 0] / U, y[:, 1] / U, y[:, 2] / (0.5 * U * U), torch.log10(1 + y[:, 3] / NU)], -1)
        return _norm(y, st["sim_y_mean"], st["sim_y_std"])
    return _norm(y, st["raw_y_mean"], st["raw_y_std"])


def to_physical(out, c, similarity, st):
    """Inverse of targets."""
    key = "sim_y" if similarity else "raw_y"
    y = out * torch.tensor(st[key + "_std"], device=out.device) + torch.tensor(st[key + "_mean"], device=out.device)
    if not similarity:
        return y
    U = c["Uinf"]
    return torch.stack([y[:, 0] * U, y[:, 1] * U, y[:, 2] * (0.5 * U * U), (10 ** y[:, 3] - 1) * NU], -1)


def param_values(Re, alpha, Uinf, similarity):
    if similarity:
        a = alpha * np.pi / 180
        return np.array([np.log10(Re), np.sin(a), np.cos(a)], np.float32)
    return np.array([Re / 1e6, alpha / 10.0, Uinf / 60.0], np.float32)


def wall_force(p_af, af):
    """Pressure force on the aerofoil from pressure at its points (no shear)."""
    c0, c1 = af["af_conn"][:, 0], af["af_conn"][:, 1]
    p_cell = 0.5 * (p_af[c0] + p_af[c1])
    n_cell = 0.5 * (af["af_normals"][c0] + af["af_normals"][c1])
    return (p_cell[:, None] * n_cell * af["af_length"][:, None]).sum(0)


def force_to_coefficients(force, Uinf, alpha):
    """Force (2,) -> (C_D, C_L) in the wind frame, AirfRANS convention."""
    a = alpha * np.pi / 180
    rot = np.array([[np.cos(a), np.sin(a)], [-np.sin(a), np.cos(a)]])
    cd, cl = 2 * (rot @ np.asarray(force, np.float64)) / Uinf ** 2
    return float(cd), float(cl)


# -----------------------------------------------------------------------------

class AirfransTask:

    def __init__(self, data_dir, similarity=True, surf_weight=1.0, p_weight=1.0, n_vol_query=8000,
                 train_split="train", val_split=None, device="cuda", seed=0, state=None, train=True):
        self.data_dir = data_dir
        self.similarity = similarity
        self.surf_weight = surf_weight
        self.p_weight = p_weight
        self.n_vol_query = n_vol_query
        self.device = device
        with open(os.path.join(data_dir, "splits.json")) as f:
            self.splits = json.load(f)
        if state is None:
            with open(os.path.join(data_dir, "stats.json")) as f:
                state = json.load(f)
        self.stats = state
        self.model_args = dict(n_dim=2, point_dim=6, query_dim=8 if similarity else 7, out_dim=4,
                               n_params=N_PARAMS, param_dim=16)
        self.rng = np.random.default_rng(seed)
        self.train_cases, self.val_cases, self.queue = [], [], []
        if train:
            self.train_cases = [self.load_case(n) for n in self.splits[train_split]]
            print(f"loaded {len(self.train_cases)} {train_split} cases")
            if val_split:
                self.val_cases = [self.load_case(n, aerofoil=True) for n in self.splits[val_split]]
                print(f"loaded {len(self.val_cases)} {val_split} cases")

    def state(self):
        return self.stats

    def load_case(self, name, aerofoil=False):
        z = np.load(os.path.join(self.data_dir, "cases", name + ".npz"))
        st, dev = self.stats, self.device
        t = lambda k: torch.from_numpy(np.asarray(z[k])).to(dev)  # noqa: E731
        c = dict(name=name, Uinf=float(z["Uinf"]), alpha=float(z["alpha"]), Re=float(z["Re"]),
                 pos=t("pos"), wd=t("wd"), nrm=t("normal"), surf=t("surf"))
        c["y"] = torch.cat([t("U"), t("p")[:, None], t("nut")[:, None]], 1)
        c["points"] = token_features(c, st)
        c["block_index"] = t("block_id").long()
        lo, hi = np.array(st["bbox_lo"], np.float32), np.array(st["bbox_hi"], np.float32)
        centers = (z["block_centers"] - (lo + hi) / 2) / np.maximum((hi - lo) / 2, 1e-9)
        c["block_centers"] = torch.from_numpy(centers.astype(np.float32)).to(dev)
        key = "sim_p" if self.similarity else "raw_p"
        pv = (param_values(c["Re"], c["alpha"], c["Uinf"], self.similarity) - np.array(st[key + "_mean"], np.float32)) \
            / np.array(st[key + "_std"], np.float32)
        c["params"] = torch.from_numpy(pv.astype(np.float32)).to(dev)
        c["surf_idx"] = torch.nonzero(c["surf"]).squeeze(1)
        c["vol_idx"] = torch.nonzero(~c["surf"]).squeeze(1)
        if aerofoil:
            c["af"] = {k: np.asarray(z[k]) for k in ("af_normals", "af_length", "af_conn", "af_to_wall")}
            c["af"]["af_normals"] = c["af"]["af_normals"][:, :2]
            c["clp_true"] = force_to_coefficients(
                wall_force(np.asarray(z["p"])[np.asarray(z["surf"])][c["af"]["af_to_wall"]], c["af"]),
                c["Uinf"], c["alpha"])[1]
        return c

    def inputs(self, c):
        return c["points"], c["block_index"], c["block_centers"], c["params"]

    def get_batch(self):
        """One case: every wall point (weight surf_weight) plus n_vol_query random volume points."""
        if not self.queue:  # one epoch = one pass over the train cases in random order
            self.queue = list(self.rng.permutation(len(self.train_cases)))
        c = self.train_cases[self.queue.pop(0)]
        nv = min(self.n_vol_query, c["vol_idx"].numel())
        vidx = c["vol_idx"][torch.randperm(c["vol_idx"].numel(), device=self.device)[:nv]]
        idx = torch.cat([c["surf_idx"], vidx])
        w = torch.ones(idx.numel(), device=self.device)
        w[:c["surf_idx"].numel()] = self.surf_weight
        col_w = torch.tensor([1.0, 1.0, self.p_weight, 1.0], device=self.device)
        return dict(inputs=self.inputs(c), xq=query_features(c, idx, self.similarity, self.stats),
                    y=targets(c["y"][idx], c, self.similarity, self.stats), w=w, col_w=col_w)

    @torch.no_grad()
    def predict(self, model, c, idx=None, chunk=8192):
        """Physical u, v, p, nu_t at points idx (all points by default), as a float32 tensor."""
        if isinstance(c, str):
            c = self.load_case(c)
        if idx is None:
            idx = torch.arange(c["pos"].shape[0], device=self.device)
        with torch.autocast("cuda", dtype=torch.bfloat16):
            tokens = model.encode(*self.inputs(c))
            out = torch.cat([model.decode(query_features(c, idx[i:i + chunk], self.similarity, self.stats), tokens).float()
                             for i in range(0, idx.numel(), chunk)])
        return to_physical(out, c, self.similarity, self.stats)

    def predict_case(self, model, name):
        y = self.predict(model, name).cpu().numpy()
        return dict(u=y[:, 0], v=y[:, 1], p=y[:, 2], nut=y[:, 3])

    @torch.no_grad()
    def evaluate(self, model):
        """Validation monitor: relative L2 of the pressure-only lift coefficient over the val cases."""
        if not self.val_cases:
            return {}
        cl_true, cl_pred = [], []
        for c in self.val_cases:
            p_wall = self.predict(model, c, c["surf_idx"])[:, 2].cpu().numpy()
            cl_pred.append(force_to_coefficients(wall_force(p_wall[c["af"]["af_to_wall"]], c["af"]),
                                                 c["Uinf"], c["alpha"])[1])
            cl_true.append(c["clp_true"])
        t, p = np.array(cl_true), np.array(cl_pred)
        return dict(val_clp_relL2=float(np.linalg.norm(p - t) / np.linalg.norm(t)))


# -----------------------------------------------------------------------------
# official metrics (same post-processing as the AirfRANS / Transolver code)

def _official_force(internal, aerofoil, surf, af_to_wall):
    """AirfRANS Compute_coefficients: pressure + wall shear stress integrated over the aerofoil."""
    intern = internal.copy().compute_derivative(scalars="U", gradient="pred_grad")
    aerofoil = aerofoil.copy()
    grad = intern.point_data["pred_grad"].reshape(-1, 3, 3)[surf, :2, :2][af_to_wall]
    p_wall = intern.point_data["p"][surf][af_to_wall]
    S = 0.5 * (grad + grad.transpose(0, 2, 1))
    S = S - S.trace(axis1=1, axis2=2).reshape(-1, 1, 1) * np.eye(2)[None] / 3
    normals = -np.asarray(aerofoil.point_data["Normals"])
    wss = ((2 * NU * S) * normals[:, :2].reshape(-1, 1, 2)).sum(axis=2)
    aerofoil.point_data["wallShearStress"] = wss
    aerofoil.point_data["p"] = p_wall
    aerofoil = aerofoil.ptc(pass_point_data=True)
    length = np.asarray(aerofoil.cell_data["Length"]).reshape(-1, 1)
    wp = (-np.asarray(aerofoil.cell_data["p"])[:, None] * np.asarray(aerofoil.cell_data["Normals"])[:, :2] * length).sum(0)
    ws = (np.asarray(aerofoil.cell_data["wallShearStress"]) * length).sum(0)
    return ws - wp


def official_case_metrics(raw_dir, data_dir, name, pred, coef_norm):
    """pred: dict of physical u, v, p, nut over all mesh points. Returns the per-case record."""
    import pyvista as pv
    z = np.load(os.path.join(data_dir, "cases", name + ".npz"))
    surf, af_to_wall = np.asarray(z["surf"]), np.asarray(z["af_to_wall"]).astype(np.int64)
    Uinf, alpha = float(z["Uinf"]), float(z["alpha"])
    y_true = np.concatenate([z["U"], z["p"][:, None], z["nut"][:, None]], 1).astype(np.float64)
    y_pred = np.stack([pred[k].astype(np.float64) for k in ("u", "v", "p", "nut")], 1)
    y_pred[surf, 0] = y_pred[surf, 1] = y_pred[surf, 3] = 0.0  # no-slip, as in the official code
    mean, std = np.array(coef_norm["mean_out"]), np.array(coef_norm["std_out"])
    err = ((y_pred - mean) / (std + 1e-8) - (y_true - mean) / (std + 1e-8)) ** 2

    internal = pv.read(os.path.join(raw_dir, name, name + "_internal.vtu"))
    aerofoil = pv.read(os.path.join(raw_dir, name, name + "_aerofoil.vtp"))
    cd_t, cl_t = force_to_coefficients(_official_force(internal, aerofoil, surf, af_to_wall), Uinf, alpha)
    pi = internal.copy()
    pi.point_data["U"][:, :2] = y_pred[:, :2]
    pi.point_data["p"] = y_pred[:, 2]
    pi.point_data["nut"] = y_pred[:, 3]
    pa = aerofoil.copy()
    pa.point_data["p"] = pi.point_data["p"][surf][af_to_wall]
    pi = pi.ptc(pass_point_data=True)
    pa = pa.ptc(pass_point_data=True)
    cd_p, cl_p = force_to_coefficients(_official_force(pi, pa, surf, af_to_wall), Uinf, alpha)
    p_true, p_pred = y_true[:, 2], y_pred[:, 2]
    return dict(case=name, C_D_true=cd_t, C_L_true=cl_t, C_D_pred=cd_p, C_L_pred=cl_p,
                vol_mse_per_var=err[~surf].mean(0).tolist(), surf_mse_per_var=err[surf].mean(0).tolist(),
                vol_p_relL2=float(np.linalg.norm(p_pred[~surf] - p_true[~surf]) / np.linalg.norm(p_true[~surf])),
                surf_p_relL2=float(np.linalg.norm(p_pred[surf] - p_true[surf]) / np.linalg.norm(p_true[surf])))


def aggregate(records):
    """Set-level metrics. C_L_rel_L2 = ||dC_L||_2 / ||C_L||_2 (the Transolver paper's number)."""
    from scipy.stats import spearmanr
    get = lambda k: np.array([r[k] for r in records], np.float64)  # noqa: E731
    cd_t, cl_t, cd_p, cl_p = get("C_D_true"), get("C_L_true"), get("C_D_pred"), get("C_L_pred")
    vol = np.array([r["vol_mse_per_var"] for r in records]).mean(0)
    surf = np.array([r["surf_mse_per_var"] for r in records]).mean(0)
    return dict(n_cases=len(records),
                C_L_rel_L2=float(np.linalg.norm(cl_p - cl_t) / np.linalg.norm(cl_t)),
                C_D_rel_L2=float(np.linalg.norm(cd_p - cd_t) / np.linalg.norm(cd_t)),
                C_L_mean_rel=float(np.mean(np.abs((cl_p - cl_t) / cl_t))),
                rho_L=float(spearmanr(cl_t, cl_p)[0]), rho_D=float(spearmanr(cd_t, cd_p)[0]),
                vol_mse=float(vol.mean()), surf_mse=float(surf.mean()),
                vol_mse_per_var=vol.tolist(), surf_mse_per_var=surf.tolist(),
                vol_p_relL2=float(get("vol_p_relL2").mean()), surf_p_relL2=float(get("surf_p_relL2").mean()))

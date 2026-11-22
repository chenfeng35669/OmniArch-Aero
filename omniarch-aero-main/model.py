"""
OmniArch-Aero: an OmniArch transformer trunk that reads a mesh and answers field queries.

One case (a geometry plus one operating condition) goes through two steps.

1. encode: the mesh points are grouped into K spatial blocks and every block becomes one
   token (point-wise MLP, max-pool inside the block, plus a Fourier code of the block
   centre). A summary token and one token per scalar condition parameter are put in front,
   and the sequence runs through the OmniArch trunk.
2. decode: each query point cross-attends to the encoded sequence and is mapped to the
   output fields. Encoding runs once per case; decoding is chunked over any number of points.

The trunk blocks have exactly the shapes of the released OmniArch-base weights, so the
first n_layer blocks and the final norm are copied from it (load_omniarch).
Parameter names follow the original experiment code, so its checkpoints load unchanged.
"""

import math
from dataclasses import dataclass

import torch
import torch.nn as nn
import torch.nn.functional as F


@dataclass
class AeroConfig:
    n_dim: int = 2            # spatial dimension of the block centres
    point_dim: int = 6        # features per point that build the block tokens
    query_dim: int = 8        # features per query point
    out_dim: int = 4          # output fields per query point
    n_params: int = 3         # scalar condition parameters, one token each
    param_dim: int = 16       # each parameter value is zero-padded to this length
    n_layer: int = 8          # trunk blocks (copied from OmniArch-base)
    n_head: int = 16
    n_embd: int = 1024
    ffn: int = 2816
    n_dec_layer: int = 1      # cross-attention decoder blocks
    dec_ffn: int = 1408
    pos_freqs: int = 6        # Fourier frequencies per axis for block centres
    point_hidden: int = 64
    point_out: int = 128
    block_hidden: int = 512
    zero_init_head: bool = False  # output exactly 0 at step 0 (the model learns a residual)


class RMSNorm(nn.Module):

    def __init__(self, d, eps=1e-6):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(d))
        self.eps = eps

    def forward(self, x):
        return x * torch.rsqrt(x.pow(2).mean(-1, keepdim=True) + self.eps) * self.weight


class Block(nn.Module):
    """OmniArch trunk block: pre-norm self-attention and SwiGLU MLP, no mask, no rotary."""

    def __init__(self, n_embd, n_head, ffn):
        super().__init__()
        self.n_head = n_head
        self.n1 = RMSNorm(n_embd)
        self.n2 = RMSNorm(n_embd)
        self.qkv = nn.Linear(n_embd, 3 * n_embd, bias=False)
        self.o = nn.Linear(n_embd, n_embd, bias=False)
        self.gate_up = nn.Linear(n_embd, 2 * ffn, bias=False)
        self.down = nn.Linear(ffn, n_embd, bias=False)

    def forward(self, x):
        B, T, C = x.shape
        q, k, v = self.qkv(self.n1(x)).view(B, T, 3, self.n_head, C // self.n_head).permute(2, 0, 3, 1, 4)
        y = F.scaled_dot_product_attention(q, k, v)
        x = x + self.o(y.transpose(1, 2).reshape(B, T, C))
        g, u = self.gate_up(self.n2(x)).chunk(2, dim=-1)
        return x + self.down(F.silu(g) * u)


class CrossBlock(nn.Module):
    """Query points (Q, C) attend to the encoded tokens (1, T, C), then a SwiGLU MLP."""

    def __init__(self, n_embd, n_head, ffn):
        super().__init__()
        self.n_head = n_head
        self.q_norm = RMSNorm(n_embd)
        self.q_proj = nn.Linear(n_embd, n_embd, bias=False)
        self.kv_proj = nn.Linear(n_embd, 2 * n_embd, bias=False)
        self.o_proj = nn.Linear(n_embd, n_embd, bias=False)
        self.ffn_norm = RMSNorm(n_embd)
        self.ffn_up = nn.Linear(n_embd, 2 * ffn, bias=False)
        self.ffn_down = nn.Linear(ffn, n_embd, bias=False)

    def forward(self, q, tokens):
        Q, C = q.shape
        _, T, _ = tokens.shape
        hd = C // self.n_head
        qq = self.q_proj(self.q_norm(q)).view(1, Q, self.n_head, hd).transpose(1, 2)
        k, v = self.kv_proj(tokens).view(1, T, 2, self.n_head, hd).permute(2, 0, 3, 1, 4)
        y = F.scaled_dot_product_attention(qq, k, v)
        q = q + self.o_proj(y.transpose(1, 2).reshape(Q, C))
        g, u = self.ffn_up(self.ffn_norm(q)).chunk(2, dim=-1)
        return q + self.ffn_down(F.silu(g) * u)


class AeroNet(nn.Module):

    def __init__(self, config):
        super().__init__()
        self.config = config
        c = config
        # block tokens: point MLP -> max-pool per block -> block MLP, plus centre position
        self.point_mlp = nn.Sequential(nn.Linear(c.point_dim, c.point_hidden), nn.GELU(),
                                       nn.Linear(c.point_hidden, c.point_out))
        self.block_mlp = nn.Sequential(nn.Linear(c.point_out, c.block_hidden), nn.GELU(),
                                       nn.Linear(c.block_hidden, c.n_embd))
        self.pos_mlp = nn.Linear(2 * c.n_dim * c.pos_freqs, c.n_embd)
        # prefix tokens: one summary token, one token per condition parameter
        self.summary_token = nn.Parameter(torch.zeros(c.n_embd))
        self.param_mlp = nn.Sequential(nn.Linear(c.param_dim + 1, 64), nn.GELU(), nn.Linear(64, c.n_embd))
        self.param_type = nn.Parameter(torch.zeros(c.n_params, c.n_embd))
        # trunk (OmniArch-base shapes)
        self.blocks = nn.ModuleList([Block(c.n_embd, c.n_head, c.ffn) for _ in range(c.n_layer)])
        self.norm = RMSNorm(c.n_embd)
        # query decoder
        self.q_embed = nn.Sequential(nn.Linear(c.query_dim, c.n_embd), nn.GELU(), nn.Linear(c.n_embd, c.n_embd))
        self.dec = nn.ModuleList([CrossBlock(c.n_embd, c.n_head, c.dec_ffn) for _ in range(c.n_dec_layer)])
        self.head_norm = RMSNorm(c.n_embd)
        self.head = nn.Sequential(nn.Linear(c.n_embd, c.n_embd), nn.GELU(), nn.Linear(c.n_embd, c.out_dim))
        if c.zero_init_head:
            nn.init.zeros_(self.head[-1].weight)
            nn.init.zeros_(self.head[-1].bias)

    def num_params(self):
        return sum(p.numel() for p in self.parameters())

    def fourier(self, centers):
        """(K, n_dim) in [-1, 1] -> (K, n_dim * 2 * pos_freqs): per axis [sin f0.., cos f0..]."""
        freqs = 2.0 ** torch.arange(self.config.pos_freqs, device=centers.device, dtype=centers.dtype)
        ang = math.pi * centers[:, :, None] * freqs
        return torch.cat([ang.sin(), ang.cos()], dim=-1).flatten(1)

    def encode(self, points, block_index, block_centers, params):
        """
        points:        (M, point_dim) features of the points that build the block tokens
        block_index:   (M,) long, block id of each point in [0, K)
        block_centers: (K, n_dim) block centres scaled to [-1, 1]
        params:        (n_params,) normalised condition parameters
        returns tokens (1, 1 + n_params + K, n_embd)
        """
        c = self.config
        K = block_centers.shape[0]
        h = self.point_mlp(points)
        pooled = h.new_full((K, h.shape[-1]), -1e4)
        pooled = pooled.scatter_reduce(0, block_index[:, None].expand_as(h), h, reduce="amax", include_self=True)
        block_tok = self.block_mlp(pooled) + self.pos_mlp(self.fourier(block_centers))
        pv = params.new_zeros(c.n_params, c.param_dim)
        pv[:, 0] = params
        pm = params.new_full((c.n_params, 1), 1.0 / c.param_dim)  # valid length / param_dim
        param_tok = self.param_mlp(torch.cat([pv, pm], dim=-1)) + self.param_type
        x = torch.cat([self.summary_token[None], param_tok, block_tok], dim=0)[None]
        for block in self.blocks:
            x = block(x)
        return self.norm(x)

    def decode(self, xq, tokens):
        """xq: (Q, query_dim) -> (Q, out_dim)."""
        q = self.q_embed(xq)
        for layer in self.dec:
            q = layer(q, tokens)
        return self.head(self.head_norm(q))

    def forward(self, points, block_index, block_centers, params, xq):
        return self.decode(xq, self.encode(points, block_index, block_centers, params))


def load_omniarch(model, path):
    """Copy the first n_layer trunk blocks and the final norm from an OmniArch-base checkpoint."""
    sd = torch.load(path, map_location="cpu", weights_only=False)["model"]
    own = model.state_dict()
    keys = [k for k in own if k.startswith("blocks.") or k == "norm.weight"]
    n = 0
    with torch.no_grad():
        for k in keys:
            if k not in sd or sd[k].shape != own[k].shape:
                raise ValueError(f"OmniArch checkpoint has no tensor {k} of shape {tuple(own[k].shape)}")
            own[k].copy_(sd[k])
            n += own[k].numel()
    print(f"loaded {len(keys)} tensors ({n / 1e6:.1f}M params) from {path}")
    return n

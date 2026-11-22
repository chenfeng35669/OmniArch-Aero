"""
A task turns one dataset into what train.py, predict.py and evaluate.py need:

    task.model_args         dict of AeroConfig fields fixed by the data (dims, number of params)
    task.get_batch()        one training micro-batch on the GPU (see train.py)
    task.predict(model, c)  full-field prediction for case name c, in physical units
    task.state()            normalisation constants, stored in the checkpoint

Tasks: airfrans (2-D airfoils, Reynolds extrapolation), blade (3-D cooled turbine blade,
inlet temperature extrapolation).
"""

import heapq

import numpy as np


def get_task(name, **kwargs):
    if name == "airfrans":
        from tasks.airfrans import AirfransTask
        return AirfransTask(**kwargs)
    if name == "blade":
        from tasks.blade import BladeTask
        return BladeTask(**kwargs)
    raise ValueError(f"unknown task {name}")


def kd_blocks(pos, n_blocks):
    """Split points into n_blocks blocks of near-equal size with a k-d tree.

    The block holding the most points is always split next, at the median of its longest
    axis. Returns block_id (N,) int32 and the mean position of each block (K, dim) float32.
    """
    pos = np.ascontiguousarray(pos, np.float32)
    heap = [(-len(pos), 0, np.arange(len(pos), dtype=np.int32))]
    counter = 1
    while len(heap) < n_blocks:
        _, _, idx = heapq.heappop(heap)
        sub = pos[idx]
        axis = int(np.argmax(sub.max(0) - sub.min(0)))
        mid = len(idx) // 2
        order = np.argpartition(sub[:, axis], mid)
        for part in (idx[order[:mid]], idx[order[mid:]]):
            heapq.heappush(heap, (-len(part), counter, part))
            counter += 1
    block_id = np.empty(len(pos), np.int32)
    centers = np.empty((len(heap), pos.shape[1]), np.float32)
    for b, (_, _, idx) in enumerate(heap):
        block_id[idx] = b
        centers[b] = pos[idx].mean(0)
    return block_id, centers

# Blade data

The blade cases are CFX conjugate heat transfer solutions (`.res`) of one cooled rotor blade,
provided by the industrial partner and not redistributed. All cases share one mesh:
13,994,104 fluid nodes and 3,304,055 solid nodes. Seven converged cases are used.

| case | Tg (K) | Tc (K) | role |
|---|---|---|---|
| e3-model-600K_001 | 600.0 | 334.5 | train, prior |
| e3-model-800K_001 | 800.0 | 445.0 | train, prior |
| e3-model-1000K_001 | 1000.0 | 557.5 | train, prior |
| e3-unmodel-600K_001 | 600.0 | 401.4 | train |
| e3_redown40_001 | 683.8 | 344.0 | train |
| e3-model-1200K_001 | 1200.0 | 669.0 | test |
| e3-1616K_001 | 1616.0 | 901.0 | test (engine condition) |

## Extracted format (input of `prepare.py`)

The `.res` files were decoded once (last iteration, 3000) into `data/blade/extracted/`:

`geometry.npz`, shared by all cases

| field | shape | meaning |
|---|---|---|
| `solid_xyz` | (3304055, 3) float32, m | solid node coordinates, x is the rotation axis |
| `solid_r` | (3304055,) float32, m | radius sqrt(y^2 + z^2) |
| `fluid_xyz` | (13994104, 3) float32, m | fluid node coordinates |
| `fluid_walldist` | (13994104,) float32, m | fluid wall distance |
| `outer_nodes` | (95837,) int32 | solid nodes on the gas-side surface (region `surface Shadow`) |
| `outer_faces` | (185552, 3) int32 | gas-side surface triangles |

`case_<case>.npz`: `solid_T` (3304055,) float32 in K, plus the scalars `Tg`, `Tc` (stationary-frame
inlet total temperatures of the main and coolant flows), `mass_main`, `mass_cool`, `Ps_out`, `rpm`.
The fluid fields (`fluid_T`, `fluid_p`, `fluid_vel`) are present but not used here.

`conditions.json`: `cases.<case>.Tg`, `.Tc` and `.similarity_params` with the five similarity
numbers used as condition tokens: `mc/mm%` (coolant to main mass flow, %), `Tc/Tm`, `PR`,
`n/sqrtT`, `m*sqrtT/P`.

Two facts were checked during extraction: the area-weighted solid temperature over the
reconstructed gas-side surface matches the value CFX reports for that region to 3e-5 K in
all seven cases, and the node coordinates are bit-identical across cases.

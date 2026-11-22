"""
Poor man's configurator, as in nanoGPT. Run with
    python train.py config/airfrans.py --seed=1 --out_dir=out/airfrans_s1
A bare file name is executed as Python and overrides the globals of the calling script;
--key=value overrides one global, with the value parsed as a Python literal when possible.
Usage: exec(open('configurator.py').read()) after the defaults are defined.
"""
import sys
from ast import literal_eval

for arg in sys.argv[1:]:
    if not arg.startswith("--"):
        print(f"config file {arg}")
        exec(open(arg).read())
    else:
        key, val = arg[2:].split("=", 1)
        if key not in globals():
            raise ValueError(f"unknown config key {key}")
        try:
            val = literal_eval(val)
        except (SyntaxError, ValueError):
            pass
        if globals()[key] is not None and val is not None and not isinstance(val, type(globals()[key])):
            if not (isinstance(globals()[key], float) and isinstance(val, int)):
                raise TypeError(f"{key}: expected {type(globals()[key]).__name__}, got {val!r}")
            val = float(val)
        print(f"override {key} = {val!r}")
        globals()[key] = val

# Plain OmniArch arm on AirfRANS: same model and schedule, dimensional inputs and outputs.
# Reported: test C_L relative L2 0.0514 +- 0.0038 over seeds 0, 1, 2.
exec(open("config/airfrans.py").read())
out_dir = "out/airfrans_raw"
similarity = False
surf_weight = 1.0
p_weight = 1.0

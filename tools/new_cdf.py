import json
import re
from glob import glob
from plot import line

boxplot_data = {}
for file in glob("asn_domain_intercept_*_k7*_heatmap.json"):
    match = re.search("_([a-z0-9]+)_k([0-9])_(dns_r1)?", file)
    system, k, dns = match.groups()
    with open(file) as f:
        heatmap_data = json.load(f)
    heatmap_data = [list(row) for row in zip(*heatmap_data)]
    boxplot_name = f"LE{' DNS' if dns is not None else ''}" if system == "le" else f"{system.upper()}{' DNS' if dns is not None else ''}"
    boxplot_data[boxplot_name] = boxplot_data.get(boxplot_name, []) + [x for row in heatmap_data for x in row if x > 0]

boxplot_data = dict(sorted(boxplot_data.items(), key=lambda x: x[0]))

cdf_data = {name: {} for name in boxplot_data.keys()}
for name, data in boxplot_data.items():
    for val in data:
        cdf_data[name][val] = cdf_data[name].get(val, 0) + 1
    for val in cdf_data[name].keys():
        cdf_data[name][val] /= len(data)

cdf_data = {name: [sum(y for x, y in cdf_data[name].items() if i >= x) for i in range(101)] for name in cdf_data.keys()}
style = {name: ("--" if "DNS" in name else "-", {"LE": "#555c9d", "TOR": "#ff8c78", "AWS30": "#842c61"}[name.split()[0]]) for name
         in cdf_data.keys()}
line(x=list(range(101)), y=cdf_data, title="CDF of % Validators Intercepted", xlabel="% validators intercepted", ylabel="CDF of on-path ASNs", xlim=(0, 100), ylim=(0.0, 1.0), side_legend=True, style=style)
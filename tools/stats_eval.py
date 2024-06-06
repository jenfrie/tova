#!/usr/bin/env python3
import json
import re
from argparse import Namespace, ArgumentParser
from datetime import datetime
from json import JSONDecodeError
from typing import List, Tuple

from humanfriendly import parse_size, format_size

from plot import container_stats, line


def main(data: Tuple[str, dict]):
    plot_stat_comparison(["NetIO In", "NetIO Out"], "bytes", data)
    plot_stat_comparison(["CPUPerc"], "% cpu usage", data)
    plot_stat_comparison(["MemUsage"], "bytes", data)

    for filename, stats in data:
        plot_single_stat("MemUsage", "bytes", stats, filename=filename)
        plot_single_stat("CPUPerc", "% cpu usage", stats, filename=filename)
        # plot_single_stat("MemPerc", "% mem usage", stats, name=name)
        # plot_single_stat("PIDs", "# processes", stats, name=name)
        # plot_single_stat("NetIO In", "bytes", stats, name=name)
        # plot_single_stat("NetIO Out", "bytes", stats, name=name)
        plot_double_stat("NetIO In", "NetIO Out", "bytes", stats, filename=filename)
        # plot_single_stat("BlockIO In", "bytes", stats, name=name)
        plot_single_stat("BlockIO Out", "bytes", stats, filename=filename)
        # plot_double_stat("BlockIO In", "BlockIO Out", "bytes", stats, name=name)
        summary(stats, filename=filename)


def summary(stats: dict, filename: str = ""):
    names = set(list(stats.values())[0].keys())
    rates = {stat_key: {name: bytes_per_sec(name, stat_key, stats) for name in names} for stat_key in ("NetIO In", "NetIO Out", "BlockIO In", "BlockIO Out")}
    totals = {stat_key: {name: stats[max(stats.keys())][name][stat_key] for name in names} for stat_key in ("NetIO In", "NetIO Out", "BlockIO In", "BlockIO Out")}

    r_min_net_in = min(rates["NetIO In"][name] for name in names)
    r_max_net_in = max(rates["NetIO In"][name] for name in names)
    r_total_net_in = sum(rates["NetIO In"][name] for name in names)

    t_min_net_in = min(totals["NetIO In"][name] for name in names)
    t_max_net_in = max(totals["NetIO In"][name] for name in names)
    t_total_net_in = sum(totals["NetIO In"][name] for name in names)

    r_min_net_out = min(rates["NetIO Out"][name] for name in names)
    r_max_net_out = max(rates["NetIO Out"][name] for name in names)
    r_total_net_out = sum(rates["NetIO Out"][name] for name in names)

    t_min_net_out = min(totals["NetIO Out"][name] for name in names)
    t_max_net_out = max(totals["NetIO Out"][name] for name in names)
    t_total_net_out = sum(totals["NetIO Out"][name] for name in names)

    r_min_net = min(rates["NetIO In"][name] + rates["NetIO Out"][name] for name in names)
    r_max_net = max(rates["NetIO In"][name] + rates["NetIO Out"][name] for name in names)
    r_total_net = sum(rates["NetIO In"][name] + rates["NetIO Out"][name] for name in names)

    t_min_net = min(totals["NetIO In"][name] + totals["NetIO Out"][name] for name in names)
    t_max_net = max(totals["NetIO In"][name] + totals["NetIO Out"][name] for name in names)
    t_total_net = sum(totals["NetIO In"][name] + totals["NetIO Out"][name] for name in names)

    r_min_block_in = min(rates["BlockIO In"][name] for name in names)
    r_max_block_in = max(rates["BlockIO In"][name] for name in names)
    r_total_block_in = sum(rates["BlockIO In"][name] for name in names)

    t_min_block_in = min(totals["BlockIO In"][name] for name in names)
    t_max_block_in = max(totals["BlockIO In"][name] for name in names)
    t_total_block_in = sum(totals["BlockIO In"][name] for name in names)

    r_min_block_out = min(rates["BlockIO Out"][name] for name in names)
    r_max_block_out = max(rates["BlockIO Out"][name] for name in names)
    r_total_block_out = sum(rates["BlockIO Out"][name] for name in names)

    t_min_block_out = min(totals["BlockIO Out"][name] for name in names)
    t_max_block_out = max(totals["BlockIO Out"][name] for name in names)
    t_total_block_out = sum(totals["BlockIO Out"][name] for name in names)

    r_min_block = min(rates["BlockIO In"][name] + rates["BlockIO Out"][name] for name in names)
    r_max_block = max(rates["BlockIO In"][name] + rates["BlockIO Out"][name] for name in names)
    r_total_block = sum(rates["BlockIO In"][name] + rates["BlockIO Out"][name] for name in names)

    t_min_block = min(totals["BlockIO In"][name] + totals["BlockIO Out"][name] for name in names)
    t_max_block = max(totals["BlockIO In"][name] + totals["BlockIO Out"][name] for name in names)
    t_total_block = sum(totals["BlockIO In"][name] + totals["BlockIO Out"][name] for name in names)

    avg_mem_per_cont = round(sum(sum(stats[timestamp][name]["MemUsage"] for name in names) / len(names) for timestamp in stats.keys()) / len(stats))
    max_mem_per_cont = max(stats[timestamp][name]["MemUsage"] for timestamp in stats.keys() for name in names)
    avg_mem_total = round(sum(sum(stats[timestamp][name]["MemUsage"] for name in names) for timestamp in stats.keys()) / len(stats))
    max_mem_total = max(sum(stats[timestamp][name]["MemUsage"] for name in names) for timestamp in stats.keys())

    if filename:
        print(f"=== {filename} ===")
    print(f"Containers: {len(names - {'avg'})}")
    print("Time:")
    print(f"    start:    {min(stats.keys()).isoformat()}")
    print(f"      end:    {max(stats.keys()).isoformat()}")
    print(f"      sec:    {round((max(stats.keys()) - min(stats.keys())).total_seconds())}")
    print("NetIO rates:")
    print(f"        I:    {format_size(r_min_net_in)}/s - {format_size(r_max_net_in)}/s per container, {format_size(r_total_net_in)}/s overall")
    print(f"        O:    {format_size(r_min_net_out)}/s - {format_size(r_max_net_out)}/s per container, {format_size(r_total_net_out)}/s overall")
    print(f"       IO:    {format_size(r_min_net)}/s - {format_size(r_max_net)}/s per container, {format_size(r_total_net)}/s overall")
    print("NetIO totals:")
    print(f"        I:    {format_size(t_min_net_in)} - {format_size(t_max_net_in)} per container, {format_size(t_total_net_in)} overall")
    print(f"        O:    {format_size(t_min_net_out)} - {format_size(t_max_net_out)} per container, {format_size(t_total_net_out)} overall")
    print(f"       IO:    {format_size(t_min_net)} - {format_size(t_max_net)}/s per container, {format_size(t_total_net)} overall")
    print("BlockIO rates:")
    print(f"        I:    {format_size(r_min_block_in)}/s - {format_size(r_max_block_in)}/s per container, {format_size(r_total_block_in)}/s overall")
    print(f"        O:    {format_size(r_min_block_out)}/s - {format_size(r_max_block_out)}/s per container, {format_size(r_total_block_out)}/s overall")
    print(f"       IO:    {format_size(r_min_block)}/s - {format_size(r_max_block)}/s per container, {format_size(r_total_block)}/s overall")
    print("BlockIO totals:")
    print(f"        I:    {format_size(t_min_block_in)} - {format_size(t_max_block_in)} per container, {format_size(t_total_block_in)} overall")
    print(f"        O:    {format_size(t_min_block_out)} - {format_size(t_max_block_out)} per container, {format_size(t_total_block_out)} overall")
    print(f"       IO:    {format_size(t_min_block)} - {format_size(t_max_block)}t per container, {format_size(t_total_block)} overall")
    print("MemUsage:")
    print(f"      Avg:    {format_size(avg_mem_per_cont)} per container, {format_size(avg_mem_total)} overall")
    print(f"      Max:    {format_size(max_mem_per_cont)} per container, {format_size(max_mem_total)} overall")
    print()


def bytes_per_sec(name: str, stat_key: str, stats: dict) -> int:
    return round(stats[max(stats.keys())][name][stat_key] / (max(stats.keys()) - min(stats.keys())).total_seconds())


def byte_totals(name: str, stat_key: str, stats: dict) -> int:
    return round(sum(stats[timestamp][name][stat_key] for timestamp in stats.keys()) / (max(stats.keys()) - min(stats.keys())).total_seconds())


def plot_single_stat(stat_key: str, stat_unit: str, stats: dict, filename: str = ""):
    x = [(d - min(stats.keys())).total_seconds() for d in stats.keys()]
    y = {name: [stats[timestamp][name][stat_key] for timestamp in stats.keys()] for name in list(stats.values())[0].keys()}
    container_stats(x, y, title=f"{filename + ' - ' if filename else ''}{stat_key} per Container", xlabel="time", ylabel=stat_unit)


def plot_double_stat(stat1_key: str, stat2_key: str, stat_unit: str, stats: dict, filename: str = ""):
    x = [(d - min(stats.keys())).total_seconds() for d in stats.keys()]
    y1 = {f"{name} ({stat1_key})": [stats[timestamp][name][stat1_key] for timestamp in stats.keys()] for name in list(stats.values())[0].keys()}
    y2 = {f"{name} ({stat2_key})": [stats[timestamp][name][stat2_key] for timestamp in stats.keys()] for name in list(stats.values())[0].keys()}
    container_stats(x, dict(y1, **y2), title=f"{filename + ' - ' if filename else ''}{stat1_key}/{stat2_key} per Container", xlabel="time", ylabel=stat_unit)


def plot_stat_comparison(stat_keys: List[str], stat_unit: str, data: Tuple[str, dict]):
    x = {filename: [(timestamp - min(stats.keys())).total_seconds() for timestamp in stats.keys()] for filename, stats in data}
    y = {filename: (x[filename], [sum(stats[timestamp][name][stat_key] for name in stats[timestamp].keys() for stat_key in stat_keys) for timestamp in stats.keys()]) for filename, stats in data}
    line([0], y, title=f"{'/'.join(stat_keys)}", xlabel="time", ylabel=stat_unit, x_is_td=True)


def parse_args() -> Namespace:
    parser = ArgumentParser(description="evaluate docker stats")
    parser.add_argument("stats", metavar="FILE", nargs="+", type=parse_stats_log, help="docker stats log")
    return parser.parse_args()


def parse_stats_log(filename: str) -> Tuple[str, dict]:
    data = {}
    current_timestamp = None
    for line in read_lines(filename):
        try:
            current_timestamp = datetime.fromisoformat(line)
        except ValueError:
            try:
                stats_line = json.loads(line)
                data.setdefault(current_timestamp, {})
                data[current_timestamp][stats_line["Name"]] = parse_numbers(stats_line)
                del data[current_timestamp][stats_line["Name"]]["Name"]
            except JSONDecodeError:
                pass
    return filename.split("/")[-1].split(".")[0], data


def de_sci_not(s: str) -> str:
    return re.sub("e\+([0-9]+)", lambda m: "0" * int(m.group(1)), s)


def read_lines(filename: str) -> List[str]:
    with open(filename) as f:
        return [line.strip() for line in f]


def parse_numbers(stats_line: dict) -> dict:
    stats_line["BlockIO In"], stats_line["BlockIO Out"] = [parse_size(de_sci_not(size)) for size in  stats_line["BlockIO"].split(" / ")]
    del stats_line["BlockIO"]
    stats_line["NetIO In"], stats_line["NetIO Out"] = [parse_size(de_sci_not(size)) for size in stats_line["NetIO"].split(" / ")]
    del stats_line["NetIO"]
    stats_line["MemUsage"], stats_line["MaxMem"] = [parse_size(de_sci_not(size)) for size in stats_line["MemUsage"].split(" / ")]
    stats_line["PIDs"] = int(stats_line["PIDs"])
    stats_line["MemPerc"] = float(stats_line["MemPerc"].rstrip("%"))
    stats_line["CPUPerc"] = float(stats_line["CPUPerc"].rstrip("%"))
    del stats_line["Container"]
    del stats_line["ID"]
    return stats_line


if __name__ == '__main__':
    args = parse_args()
    main(args.stats)

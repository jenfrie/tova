#!/usr/bin/env python3
import json
from argparse import Namespace, ArgumentParser
from typing import Tuple, List, Dict

from tqdm import tqdm

from plot import boxplot, hist, scatter


def main(data: dict, domains: List[str]):
    with tqdm(desc="plotting", total=3, leave=True) as prog:
        val_duration = validation_duration(data)
        boxplot(val_duration, title="Validation Duration", xlabel="seconds", ylabel="# validators", horizontal=True, show_outliers=False)
        prog.write("validation duration\n" + "\n".join(f"{name}: {round(sum(values) / len(values), ndigits=1)}s avg." for name, values in val_duration.items()) + "\n")
        prog.update()

        val_prog = validation_progress(data, domains)
        scatter(x=[0], y=val_prog, title="Validation Progress", xlabel="time", ylabel="# validations", x_is_td=True)
        prog.write("validation speed\n" + "\n".join(f"{name}: {round(n[-1] / (t[-1] or 1), ndigits=2)} val/s" for name, (t, n) in val_prog.items()) + "\n")
        prog.update()

        x, y = n_validators(data)
        hist(x, y, title="Histogram of Validators Used", xlabel="# validators", ylabel="% validations", perc=True)
        prog.write("validators used\n" + "\n".join(f"{name}: {min(x[i] for i in range(len(x)) if h[i] != 0)} - {max(x[i] for i in range(len(x)) if h[i] != 0)} validators/val" for name, h in y.items()) + "\n")
        prog.update()

        # timeouts = request_timeouts(data)
        # line(x=[0], y=timeouts, title="Validator Request Timeouts", xlabel="time", ylabel="# timeouts", x_is_td=True)
        # prog.write("request timeouts\n" + "\n".join(f"{name}: {round(n[-1] / (t[-1] or 1), ndigits=2)} timeouts/s" for name, (t, n) in timeouts.items()) + "\n")
        # prog.update()

        print()


def validation_duration(data: dict) -> dict:
    val_duration = {name: [] for name in data.keys()}
    for name, lines in data.items():
        for line in sorted(lines, key=lambda x: x.get("req_start", 0)):
            try:
                val_duration[name].append(line["req_end"] - line["req_start"])
            except KeyError:
                pass
    return val_duration


def validation_progress(data: dict, domains: List[str]) -> dict:
    start_time = {name: 0 for name in data.keys()}
    val_prog = {name: [(0, 0)] for name in data.keys()}

    if domains:
        domain_starts = {name: {line["domain"]: line["req_start"] for line in lines} for name, lines in data.items()}
        for name in data.keys():
            for timeout_domain in set(domains) - set(domain_starts[name].keys()):
                ind, i = domains.index(timeout_domain), 1
                try:
                    closest_start = None
                    while not closest_start:
                        closest_start = domain_starts[name].get(domains[max(0, ind - i)]) or domain_starts[name].get(domains[ind + i])
                        i += 1
                    data[name].append({"req_start": closest_start, "rq_end": closest_start + 60, "domain": timeout_domain, "timeout": True})
                except IndexError:
                    pass

    for name, lines in data.items():
        for line in sorted(lines, key=lambda x: x.get("req_start", 0)):
            try:
                start_time[name] = line["req_start"]
                break
            except KeyError:
                pass

    for name, lines in data.items():
        for prog, line in enumerate(sorted(lines, key=lambda x: x.get("req_start", 0))):
            try:
                if not line.get("timeout"):
                    val_prog[name].append((line["req_end"] - start_time[name], prog + 1))
            except KeyError:
                pass
    return {name: tuple(zip(*values)) for name, values in val_prog.items()}


def n_validators(data: dict) -> Tuple[List[int], Dict[str, List[int]]]:
    n_val = {name: {} for name in data.keys()}
    for name, lines in data.items():
        for line in sorted(lines, key=lambda x: x.get("req_start", 0)):
            try:
                k = len(line["exit_target_pairs"])
                n_val[name][k] = n_val[name].get(k, 0) + 1
            except KeyError:
                pass
    x = sorted({v for hist in n_val.values() for v in hist.keys()})
    y = {name: [hist.get(k, 0) for k in x] for name, hist in n_val.items()}
    return x, y


def request_timeouts(data: dict) -> dict:
    start_time = {name: 0 for name in data.keys()}
    timeouts = {name: [(0, 0)] for name in data.keys()}

    for name, lines in data.items():
        for line in sorted(lines, key=lambda x: x.get("req_start", 0)):
            try:
                start_time[name] = line["req_start"]
                break
            except KeyError:
                pass

    current_time = {name: start_time[name] for name in data.keys()}
    for name, lines in data.items():
        for line in sorted(lines, key=lambda x: x.get("req_start", 0)):
            current_time[name] = line.get("req_end", current_time[name])
            try:
                if "Timeout" in line.get("error", ""):
                    timeouts[name].append((current_time[name] - start_time[name], timeouts[name][-1][1] + 1))
            except KeyError:
                pass
    return {name: tuple(zip(*values)) for name, values in timeouts.items()}


def parse_args() -> Namespace:
    parser = ArgumentParser(description="evaluate app.log from tova docker container")
    parser.add_argument("logs", nargs="+", metavar="FILE", type=load_jsonl, help="app.log files in .jsonl format")
    parser.add_argument("--domains", metavar="FILE", type=read_lines, default=[], help="list of domains queried")
    return parser.parse_args()


def load_jsonl(filename: str) -> dict:
    with open(filename) as f:
        return {filename.split("/")[-1].split(".")[0]: [json.loads(line.strip()) for line in f]}


def read_lines(filename: str) -> List[str]:
    with open(filename) as f:
        return [line.strip() for line in f]


if __name__ == '__main__':
    print("reading data...\n")
    args = parse_args()
    data = {}
    for log in args.logs:
        data.update(log)
    main(data, args.domains)

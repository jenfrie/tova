#!/usr/bin/env python3
import json
import re
from argparse import Namespace, ArgumentParser
from typing import Tuple, List

from tqdm import tqdm

from plot import boxplot, hist


VAL_K = 5


def main(data: dict):
    with tqdm(desc="plotting", total=5, leave=True) as prog:
        # val_duration = validation_duration(data)
        # boxplot(val_duration, title="Validation Duration", xlabel="seconds", ylabel="# validators", horizontal=True, show_outliers=False)
        # prog.write("validation duration\n" + "\n".join(f"{name}: {round(sum(values) / len(values), ndigits=1)}s avg." for name, values in val_duration.items()) + "\n")
        # prog.update()
        #
        # labels, blocked_counts = tor_blocking(data)
        # hist(labels, blocked_counts, title="Rates of Errors Indicating Blocking of Tor", xlabel="error", ylabel="% requests")
        # prog.write("tor blocking\n" + "\n".join(f"{name}: {sum(err)}%" for name, err in blocked_counts.items()) + "\n")
        # prog.update()
        #
        # labels, err_rates = error_rates(data)
        # hist(labels, err_rates, title="Distribution of Errors Per Validation", xlabel="# errors", ylabel="% validations")
        # prog.write("error rates\n" + "\n".join(f"{name}: {round(100 - sum(err_rates[name][:VAL_K]), ndigits=1)}% with full failure" for name, err in err_rates.items()) + "\n")
        # prog.update()

        sizes = response_size(data)
        prog.write("response sizes\n" + "\n".join(f"{name}: {round(sum(size_list) / len(size_list))} B" for name, size_list in sizes.items()))
        prog.write(f"total: {round(sum(sum(sizelist) for sizelist in sizes.values()) / sum(len(sizelist) for sizelist in sizes.values()))} B\n")
        prog.update()

        redirect_rates = redirects(data)
        prog.write("redirect rate\n" + "\n".join(f"{name}: {pct}%" for name, pct in redirect_rates.items()))
        prog.update()



def validation_duration(data: dict) -> dict:
    val_duration = {name: [] for name in data.keys()}
    for name, lines in data.items():
        for line in sorted(lines, key=lambda x: x.get("req_start", 0)):
            try:
                val_duration[name].append(line["req_end"] - line["req_start"])
            except KeyError:
                pass
    return val_duration


def tor_blocking(data: dict) -> Tuple[List[str], dict]:
    errors = {"ConnectTimeout", "ConnectionError"}
    blocked = {name: {err: 0 for err in errors} for name in data.keys()}
    total = {name: 0 for name in data.keys()}

    for name, lines in data.items():
        for line in lines:
            for _, _, result in line["results"]:
                total[name] += 1
                try:
                    err = re.search("ERR: <class 'requests\.exceptions\.([a-zA-Z]+)'>", result).group(1)
                    blocked[name][err] += 1
                except (AttributeError, KeyError):
                    pass
    return list(errors), {name: [round(100 * count / total[name], ndigits=2) for count in err.values()] for name, err in blocked.items()}


def error_rates(data: dict) -> Tuple[List[int], dict]:
    err_strings = {f"ERR: <class 'requests.exceptions.{err}'>" for err in ["ConnectTimeout", "ConnectionError"]}
    err_counts = {name: {} for name in data.keys()}
    total = {name: 0 for name in data.keys()}

    for name, lines in data.items():
        for line in lines:
            total[name] += 1
            n_errors = sum(result in err_strings for _, _, result in line["results"])
            err_counts[name][n_errors] = err_counts[name].get(n_errors, 0) + 1
    labels = list(range(max(n for counts in err_counts.values() for n in counts.keys()) + 1))
    return labels, {name: [round(100 * counts.get(i, 0) / total[name], ndigits=1) for i in labels] for name, counts in err_counts.items()}


def response_size(data: dict) -> dict:
    sizes = {name: [] for name in data.keys()}
    for name, lines in data.items():
        for line in lines:
            size = 0
            for _, _, result in line["results"]:
                try:
                    hidden_size = int(re.search("\.\.\[([0-9]+)]\.\.", result).group(1))
                    size = len(result) + hidden_size - 6
                    break
                except AttributeError:
                    pass
            sizes[name].append(size)
    return sizes


def redirects(data: dict) -> dict:
    redirect_count = {name: 0 for name in data.keys()}
    total = {name: 0 for name in data.keys()}
    for name, lines in data.items():
        for line in lines:
            for _, _, result in line["results"]:
                if "ERR:" not in result:
                    total[name] += 1
                    if "301" in result:
                        redirect_count[name] += 1
    output = {name: round(100 * redirect_count[name] / total[name], ndigits=1) for name in data.keys()}
    output.update({"total": round(100 * sum(redirect_count.values()) / sum(total.values()), ndigits=1)})
    return output


def parse_args() -> Namespace:
    parser = ArgumentParser(description="evaluate app.log from tova docker container")
    parser.add_argument("logs", nargs="+", metavar="FILE", type=load_jsonl, help="app.log files in .jsonl format")
    return parser.parse_args()


def load_jsonl(filename: str) -> dict:
    with open(filename) as f:
        return {filename.split("/")[-1].split(".")[0]: [json.loads(line.strip()) for line in f]}


if __name__ == '__main__':
    print("reading data...\n")
    args = parse_args()
    data = {}
    for log in args.logs:
        data.update(log)
    main(data)

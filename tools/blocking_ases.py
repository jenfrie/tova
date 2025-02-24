#!/usr/bin/env python3

import json
from argparse import Namespace, ArgumentParser
from ipaddress import IPv4Network, AddressValueError, IPv6Network
from multiprocessing import Pool
import random
from typing import List, Tuple

from pybgpsim import CaidaReader, Graph, GraphSearch
from tqdm import tqdm

from plot import hist

asn_of = {}
search = None
pfx2as = None
dns = {}


def main(applog: List[dict], caida: str):
    global search, pfx2as, asn_of

    asn_pairs = []
    no_target_ip, total_results = 0, 0
    asn_type = {}
    for entry in tqdm(applog, desc="ASN pairs", total=len(applog), mininterval=5):
        for src, dest, result in entry["results"]:
            total_results += 1
            try:
                asn_of.setdefault(src, ip2asn(src))
                asn_of.setdefault(dest, ip2asn(dest or random.choice(dns[entry["domain"]]["ips"])))
                asn_pairs.append((asn_of[src], asn_of[dest], any(f"requests.exceptions.{err}" in result for err in ["ConnectTimeout", "ConnectionError", "ReadTimeout"])))
                asn_type[asn_of[src]] = "src"
                asn_type[asn_of[dest]] = "dest"
            except (KeyError, IndexError):
                no_target_ip += 1

    print(f"no target IP found for {no_target_ip} ({round(100 * no_target_ip / total_results, ndigits=1)}%) requests, ignoring")
    graph = Graph()
    reader = CaidaReader(graph)
    reader.ReadFile(caida)
    search = GraphSearch(graph)

    asn_counts = {}
    with Pool() as pool:
        for result in list(tqdm(pool.imap(get_path_asns, asn_pairs, chunksize=100), total=len(asn_pairs), desc="paths", leave=True, mininterval=10)):
            for asn, err in result.items():
                asn_counts.setdefault(asn, {"err": 0, "ok": 0})
                asn_counts[asn]["err" if err else "ok"] += 1

    for asn in asn_counts.keys():
        asn_counts[asn]["type"] = asn_type.get(asn, "transit")
    with open("tor_blocking.json", "w") as f:
        json.dump(asn_counts, f, indent=2)

    blocking_asns = sorted(asn_counts.items(), key=lambda x: x[1]["err"] - x[1]["ok"], reverse=True)[:50]
    hist(list(range(min(50, len(blocking_asns)))), {"blocked": [x[1]["err"] for x in blocking_asns], "passed": [x[1]["ok"] for x in blocking_asns]}, title="Top Tor-Blocking ASes (combined)", xlabel="AS", ylabel="# requests")
    blocking_asns = sorted([(asn, counts) for asn, counts in asn_counts.items() if counts["ok"] == 0], key=lambda x: x[1]["err"], reverse=True)[:50]
    hist(list(range(min(50, len(blocking_asns)))), [x[1]["err"] for x in blocking_asns], title="Top Tor-Blocking ASes (no-pass)", xlabel="AS", ylabel="# requests blocked")
    for asn, _ in blocking_asns:
        print(asn, asn_type.get(asn, "transit"))


def get_path_asns(args: Tuple[int, int, bool]) -> dict:
    src, dest, err = args
    return {asn: err for asn in set(search.GetPath(src, dest)).union(set(search.GetPath(dest, src))) - {src}}


def ip2asn(ip: str) -> int:
    ip = ip.lstrip("[").rstrip("]")
    try:
        return ipv42asn(ip)
    except AddressValueError:
        return ipv62asn(ip)


def ipv42asn(ip: str) -> int:
    global pfx2as
    try:
        ipnet = IPv4Network(f"{ip}/{32}", strict=False)
    except AddressValueError:
        ipnet = IPv4Network(ip, strict=False)

    while ipnet != IPv4Network("0.0.0.0/0"):
        try:
            return pfx2as[ipnet][0]
        except KeyError:
            ipnet = ipnet.supernet()
    return 0


def ipv62asn(ip: str) -> int:
    global pfx2as
    try:
        ipnet = IPv6Network(f"{ip}/{128}", strict=False)
    except AddressValueError:
        ipnet = IPv6Network(ip, strict=False)

    while ipnet != IPv6Network("::/0"):
        try:
            return pfx2as[ipnet][0]
        except KeyError:
            ipnet = ipnet.supernet()
    return 0


def parse_args() -> Namespace:
    parser = ArgumentParser(description="evaluate Tor blocking behavior of ASes")
    parser.add_argument("files", metavar="APPDATA", type=read_jsonl, nargs="+", help="app.jsonl files to evaluate")
    parser.add_argument("caida", metavar="CAIDA", help="CAIDA AS relationship file")
    parser.add_argument("pfx2as", metavar="PREFIX2AS", type=read_pfx2as, help="CAIDA Prefix2AS file")
    parser.add_argument("--dns", metavar="DNSJSON", type=read_json, nargs="+", default={}, help="dnslookup.py JSON output")
    return parser.parse_args()


def read_jsonl(filename: str) -> List[dict]:
    with open(filename) as f:
        return [json.loads(line.strip()) for line in f]


def read_pfx2as(filename: str) -> dict:
    pfx2as = {}
    with open(filename) as f:
        for line in f:
            prefix, length, asns = line.strip().split()
            try:
                pfx2as[IPv4Network(f"{prefix}/{length}")] = [int(asn) for asn in asns.split("_")]
            except (AddressValueError, ValueError):
                pass
    return pfx2as


def read_lines(filename: str) -> List[str]:
    with open(filename) as f:
        return [line.strip() for line in f]


def read_json(filename: str) -> dict:
    with open(filename) as f:
        return json.load(f)


if __name__ == '__main__':
    print("loading...")
    args = parse_args()
    applog = [entry for file in args.files for entry in file]
    pfx2as = args.pfx2as
    for table in args.dns:
        dns.update(table)

    if applog:
        main(applog, args.caida)
    else:
        print("empty input")

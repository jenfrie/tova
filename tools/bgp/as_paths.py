#!/usr/bin/env python3

import json
import random
from argparse import Namespace, ArgumentParser
from ipaddress import IPv4Network, AddressValueError, IPv6Network
from multiprocessing import Pool
from typing import List, Tuple

from pybgpsim import CaidaReader, Graph, GraphSearch
from tqdm import tqdm

asn_of = {}
search = None
pfx2as = None

main_le_ip = "23.178.112.201"
main_le_dns_ip = "23.178.112.201"
le_val_ips = ["16.16.204.159", "3.129.25.162", "13.49.137.73", "18.116.242.194", "18.237.3.70", "13.60.83.241"]
le_val_dns_ips = ["51.20.133.4", "47.129.12.135", "35.90.152.70", "18.117.157.226", "52.42.153.110", "34.217.90.242", "18.216.202.198", "16.170.207.16"]


def main(applog: List[dict], caida: str, le_sub: bool = False, dns_sub: bool = False):
    global search, pfx2as, asn_of

    src_ips, dest_ips = set(), set()
    asn_pairs = set()

    for entry in tqdm(applog, desc="ip2asn"):
        if le_sub:
            vals = [main_le_dns_ip if dns_sub else main_le_ip] + random.choices(le_val_dns_ips if dns_sub else le_val_ips, k=2)
            entry["exit_target_pairs"] = [(vals.pop(), target) for exit, target in entry["exit_target_pairs"][:3]]

        for src, dest in entry["exit_target_pairs"]:
            src_ips.add(src)
            dest_ips.add(dest)
            asn_of.setdefault(src, ip2asn(src))
            asn_of.setdefault(dest, ip2asn(dest))
            asn_pairs.add((asn_of[src], asn_of[dest]))

    graph = Graph()
    reader = CaidaReader(graph)
    reader.ReadFile(caida)
    search = GraphSearch(graph)

    on_path_asns = {}
    with Pool() as pool:
        for result in list(tqdm(pool.imap(get_on_path_asns, asn_pairs, chunksize=100), total=len(asn_pairs), desc="paths", leave=True)):
            on_path_asns.update(result)

    on_path_perc = {}
    for entry in tqdm(applog, desc="overlap"):
        on_path_perc[entry["domain"]] = {}
        for src, dest in entry["exit_target_pairs"]:
            for asn in on_path_asns[(asn_of[src], asn_of[dest])]:
                on_path_perc[entry["domain"]][asn] = on_path_perc[entry["domain"]].get(asn, 0) + 1 / len(entry["exit_target_pairs"])

    overlap_metric = round(sum(sum(asns.values()) / max(1, len(asns)) for asns in on_path_perc.values()) / len(on_path_perc), ndigits=3)

    print(f"domains:       {len({entry['domain'] for entry in applog})}")
    print(f"validators:    {len(src_ips)}")
    print(f"target IPs:    {len(dest_ips)}")
    print(f"paths:         {len(on_path_asns)}")
    print(f"overlap:       {overlap_metric}")

    hist = {}
    for domain, on_path in on_path_perc.items():
        for asn, frac in on_path.items():
            perc = round(frac, ndigits=1) * 100
            hist[perc] = hist.get(perc, 0) + 1

    with open("path_overlap_hist.json", "w") as f:
        json.dump(hist, f)


def get_on_path_asns(args: Tuple[int, int]) -> dict:
    src, dest = args
    return {(src, dest): set(search.GetPath(src, dest)).union(set(search.GetPath(dest, src))) - {src, dest}}


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
    parser = ArgumentParser(description="evaluate BGP distribution of applog data from tova container")
    parser.add_argument("files", metavar="APPDATA", type=read_jsonl, nargs="+", help="app.jsonl files to evaluate")
    parser.add_argument("caida", metavar="CAIDA", help="CAIDA AS relationship file")
    parser.add_argument("pfx2as", metavar="PREFIX2AS", type=read_pfx2as, help="CAIDA Prefix2AS file")
    parser.add_argument("--le-sub", action="store_true", default=False, help="replace validator IPs with Let's Encrypt IPs")
    parser.add_argument("--dns", action="store_true", default=False, help="do replacement with Let's Encrypt DNS resolver IPs")
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


if __name__ == '__main__':
    print("loading...")
    args = parse_args()
    applog = [entry for file in args.files for entry in file]
    pfx2as = args.pfx2as

    if applog:
        main(applog, args.caida, args.le_sub, args.dns)
    else:
        print("empty input")

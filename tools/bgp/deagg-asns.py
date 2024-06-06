#!/usr/bin/env python3

# pipe in bgpdump -m <file>.gz

import re
import subprocess
import sys
from argparse import Namespace, ArgumentParser
from typing import List, Tuple, Any, Set, Iterable

from tqdm import tqdm


def deaggregate_all_duplicate_hops(prefix_paths: List[Tuple[str, List[str]]]) -> List[Tuple[str, List[str]]]:
    for prefix, as_path in tqdm(prefix_paths, desc="deaggregating duplicate hops"):
        deaggregate_duplicate_hops(as_path)
    return prefix_paths


def deaggregate_duplicate_hops(as_path: List[str]) -> List[str]:
    p = 1
    next_hop = as_path[-1]
    for i in range(-2, -len(as_path), -1):
        if as_path[i] == next_hop:
            as_path[i] = as_path[i] + f"-p{p}"
            p += 1
        else:
            next_hop = as_path[i]
            p = 1
    return as_path


def deaggregate_origins(prefix_paths: List[Tuple[str, List[str]]]) -> List[Tuple[str, List[str]]]:
    prefix_paths.sort(key=lambda x: list(reversed(x[1])))
    trailer = 0

    for header in tqdm(range(len(prefix_paths)), total=len(prefix_paths), desc="deaggregating origins"):
        if prefix_paths[header][1][-1] == prefix_paths[trailer][1][-1]:
            continue
        deaggregate_origin(asn=prefix_paths[trailer][1][-1], prefix_paths=prefix_paths[trailer:header])
        trailer = header

    return prefix_paths


def deaggregate_origin(asn: str, prefix_paths: List[Tuple[str, List[str]]]) -> List[Tuple[str, List[str]]]:
    pfx2asns = prefix2asns(asn, prefix_paths)

    asn2pfxs = {}
    for p, a in pfx2asns.items():
        asn2pfxs[tuple(a)] = asn2pfxs.setdefault(tuple(a), set()).union({p})

    if len(asn2pfxs) > 1:
        for i in range(len(prefix_paths)):
            for j, pfxs in enumerate(asn2pfxs.values()):
                if prefix_paths[i][0] in pfxs:
                    replace_in_list(asn, asn + f"-o{j}", prefix_paths[i][1])
    return prefix_paths


def prefix2asns(asn: str, prefix_paths: List[Tuple[str, List[str]]]) -> dict:
    pfx2asn = {}
    for prefix, as_path in prefix_paths:
        as_path = remove_all_of(asn, as_path)
        try:
            pfx2asn[prefix] = pfx2asn.setdefault(prefix, set()).union({as_path[-1]})
        except IndexError:
            pfx2asn[prefix] = pfx2asn.setdefault(prefix, set()).union({asn})
    return pfx2asn


def remove_all_of(r: str, l: List[str]) -> List[str]:
    return [x for x in l if x != r]


def replace_in_list(target: Any, replacement: Any, l: List[Any]):
    for i in range(len(l)):
        if l[i] == target:
            l[i] = replacement


def get_edges(prefix_paths: List[Tuple[str, List[str]]]) -> Set[Tuple[str, str]]:
    return {tuple(as_path[i:i + 2]) for _, as_path in tqdm(prefix_paths, desc="determining AS edges") for i in range(len(as_path) - 1)}


def get_pfx2as_mapping(prefix_paths: List[Tuple[str, List[str]]]) -> Set[Tuple[str, str, str]]:
    return {tuple(prefix.split("/")) + as_path[-1:] for prefix, as_path in tqdm(prefix_paths, desc="determining prefix2as mapping")}


def parse_bgpdump_line(line: str) -> Tuple[str, List[str]]:
    match = re.search("\|([0-9a-f:.]+/[0-9]+)\|([0-9 ]+)( {|\|)", line)
    return match.group(1), match.group(2).split()


def parse_args() -> Namespace:
    parser = ArgumentParser(description="Deaggregate originating ASNs based on AS path and individualize artificially lengthened AS paths. "
                                        "Note: should be post-processed with 'sort | uniq'.")
    parser.add_argument("--bgpdump", "-b", default="-", help="file containing output of 'bgpdump -m <file>' (default: stdin)")
    parser.add_argument("--edges-out", "-e", default="edges.tsv", help="write AS edges to specified file (default: %(default)s)")
    parser.add_argument("--pfx2as-out", "-p", default="pfx2as.tsv", help="write prefix-to-AS mapping to specified file (default: %(default)s)")
    parser.add_argument("--raw", "-r", action="store_true", help="output deaggregated AS path per prefix without writing files")
    return parser.parse_args()


def parse_lines(source: str) -> List[Tuple[str, List[str]]]:
    lines = sys.stdin if source == "-" else open(source)
    n_lines = None if args.bgpdump == "-" else get_line_count(args.bgpdump)
    return [parse_bgpdump_line(line) for line in tqdm(lines, desc="parsing", total=n_lines)]


def get_line_count(filename: str) -> int:
    p = subprocess.run(f"wc -l {filename}", shell=True, stdout=subprocess.PIPE)
    return int(p.stdout.decode().split()[0])


def write_debug_output(prefix_paths: List[Tuple[str, List[str]]]):
    for prefix, as_path in prefix_paths:
        print(f"{prefix}\t{','.join(as_path)}")


def write_output(edges_file: str, pfx2as_file: str, prefix_paths: List[Tuple[str, List[str]]]):
    with open(edges_file, "w") as f_edges:
        with open(pfx2as_file, "w") as f_pfx2as:
            for prefix, as_path in tqdm(prefix_paths, desc="writing edges & prefix2as mapping"):

                f_pfx2as.write("\t".join(prefix.split("/") + as_path[-1:]) + "\n")

                for i in range(len(as_path) - 1):
                    f_edges.write("\t".join(as_path[i:i + 2]) + "\n")


if __name__ == '__main__':
    args = parse_args()

    lines = sys.stdin if args.bgpdump == "-" else open(args.bgpdump)
    prefix_paths = parse_lines(args.bgpdump)
    lines.close()

    deaggregate_origins(prefix_paths)
    # deaggregate_all_duplicate_hops(prefix_paths)

    if args.raw:
        write_debug_output(prefix_paths)

    else:
        write_output(edges_file=args.edges_out, pfx2as_file=args.pfx2as_out, prefix_paths=prefix_paths)

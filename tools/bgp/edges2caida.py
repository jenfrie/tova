#!/usr/bin/env python3
import sys
from argparse import Namespace, ArgumentParser
from pathlib import Path
from typing import List, Tuple, Dict

from tqdm import tqdm


def parse_args() -> Namespace:
    parser = ArgumentParser(description="Apply CAIDA AS relationships to AS edges (resulting CAIDA file written to stdout)")
    parser.add_argument("--edges", "-e", metavar="FILE", required=True, help="file containing edges")
    parser.add_argument("--caida", "-c", metavar="FILE", required=True, help="CAIDA AS relationship file")
    return parser.parse_args()


def read_caida(filename: str) -> Dict[Tuple[int, int], int]:
    return {(int(asn1), int(asn2)): int(rel) for line in read_lines(filename) if not line.startswith("#") for asn1, asn2, rel, _ in [line.split("|")]}


def read_edges(filename: str) -> List[Tuple[str, ...]]:
    return [tuple(line.split()) for line in read_lines(filename)]


def read_lines(filename: str) -> List[str]:
    return Path(filename).read_text().split("\n")[:-1]


def get_rel(caida: Dict[Tuple[int, int], int], vasn1: str, vasn2: str) -> int:
    asn1 = int(vasn1.split("-")[0])
    asn2 = int(vasn2.split("-")[0])

    if asn1 == asn2:
        return 0
    try:
        return caida[(asn1, asn2)]
    except KeyError:
        try:
            return caida[(asn2, asn1)] * 2
        except KeyError:
            return 0


def write_caida_edge(asn1: str, asn2: str, rel: int):
    print(f"{asn1}|{asn2}|{rel}|bgp")


if __name__ == '__main__':
    args = parse_args()
    print("loading files ...", file=sys.stderr)
    caida = read_caida(args.caida)
    edges = read_edges(args.edges)

    for vasn1, vasn2 in tqdm(edges, desc="applying CAIDA relationships"):
        rel = get_rel(caida, vasn1, vasn2)
        if rel == -2:
            vasn2, vasn1 = (vasn1, vasn2)
        write_caida_edge(vasn1, vasn2, rel)

#!/usr/bin/env python3
import sys
from argparse import Namespace, ArgumentParser
from os.path import basename
from pathlib import Path
from typing import List


def parse_args() -> Namespace:
    parser = ArgumentParser(description="Map deaggregated ASN strings to virtual ASN integers (writes 'intified' CAIDA and pfx2as files)")
    parser.add_argument("--pfx2as", "-p", metavar="FILE", help="file containing prefix-to-AS mapping")
    parser.add_argument("--caida", "-c", metavar="FILE", help="CAIDA AS relationship file")
    return parser.parse_args()


def parse_fields(lines: List[str], split_char: str = None) -> List[List[str]]:
    return [line.split(split_char) for line in lines]


def read_lines(filename: str) -> List[str]:
    return Path(filename).read_text().split("\n")[:-1]


if __name__ == '__main__':
    args = parse_args()
    if not args.caida and not args.pfx2as:
        print("no input (see --help)", file=sys.stderr)
        exit(1)

    caida_lines = parse_fields(read_lines(args.caida), split_char="|") if args.caida else []
    pfx2as_lines = parse_fields(read_lines(args.pfx2as)) if args.pfx2as else []

    asns = {asn for line in caida_lines for asn in line[:2]}
    asns = asns.union({line[-1] for line in pfx2as_lines})
    intify = {asn: str(i + 1) for i, asn in enumerate(asns)}

    if args.caida:
        Path("intified_" + basename(args.caida)).write_text("\n".join("|".join([intify[asn1], intify[asn2], rel, bgp]) for asn1, asn2, rel, bgp in caida_lines) + "\n")

    if args.pfx2as:
        Path("intified_" + basename(args.pfx2as)).write_text("\n".join("\t".join([prefix, prefix_len, intify[asn]]) for prefix, prefix_len, asn in pfx2as_lines) + "\n")

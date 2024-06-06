#!/usr/bin/env python3
import sys
from ipaddress import AddressValueError, IPv4Network
from typing import List


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


def ip2asn(pfx2as: dict, ip: str) -> List[int]:
    try:
        ipnet = IPv4Network(f"{ip}/{32}", strict=False)
    except AddressValueError:
        ipnet = IPv4Network(ip, strict=False)

    while ipnet != IPv4Network("0.0.0.0/0"):
        try:
            return pfx2as[ipnet]
        except KeyError:
            ipnet = ipnet.supernet()
    return []


if __name__ == '__main__':
    pfx2as = read_pfx2as(sys.argv[1])
    for ip in sys.stdin:
        print(*ip2asn(pfx2as, ip.strip()))

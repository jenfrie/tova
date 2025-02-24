#!/usr/bin/env python3
import json
from argparse import Namespace, ArgumentParser
from multiprocessing.pool import ThreadPool
from typing import Set, Tuple

from dns.exception import DNSException
from dns.resolver import Resolver
from tqdm import tqdm

resolver = Resolver()
resolver.nameservers = ["1.1.1.1", "1.0.0.1", # cloudflare
                        "9.9.9.9", "149.112.112.112", # quad9
                        "8.8.8.8", "8.8.4.4", # google
                        "208.67.222.222", "208.67.220.220"] # opendns


def main(domains: Set[str]):
    results = {}
    with ThreadPool(len(resolver.nameservers)) as pool:
        for domain, dns in list(tqdm(pool.imap(dns_lookup, domains), total=len(domains), desc="DNS lookup")):
            if dns:
                results.update({domain: dns})

    with open(f"dnslookup.json", "w") as f:
        json.dump(results, f, indent=2)


def dns_lookup(domain: str) -> Tuple[str, dict]:
    cnames, ips = [], []
    try:
        cnames = [record.to_text().rstrip(".") for record in resolver.resolve(domain, "CNAME").rrset]
    except DNSException:
        pass
    try:
        ips = [record.address for record in resolver.resolve(domain, "A").rrset]
    except DNSException:
        pass

    return domain, {"ips": ips, "cnames": cnames} if cnames or ips else {}


def parse_args() -> Namespace:
    parser = ArgumentParser(description="look up CNAME and A records for list of domains")
    parser.add_argument("domains", type=read_lines, help="domains to lookup")
    return parser.parse_args()


def read_lines(filename: str) -> Set[str]:
    with open(filename, encoding="ascii", errors="ignore") as f:
        return {l.strip() for l in f}

if __name__ == '__main__':
    args = parse_args()
    main(args.domains)

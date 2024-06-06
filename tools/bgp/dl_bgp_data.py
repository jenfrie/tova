#!/usr/bin/env python3

import re
from argparse import Namespace, ArgumentParser
from datetime import datetime
from typing import Tuple

import requests


def main():
    today = datetime.today()
    ripe_date_str = datetime.strftime(today, "%Y.%m")
    caida_date_str = datetime.strftime(today, "%Y/%m")

    # BGP Dumps
    dl_latest_file(base_url=f"https://data.ris.ripe.net/rrc00/{ripe_date_str}/", file_regex=r"bview.[0-9]{8}\.[0-9]{4}\.gz", file_prefix="rcc00_")
    dl_latest_file(base_url=f"https://data.ris.ripe.net/rrc24/{ripe_date_str}/", file_regex=r"bview.[0-9]{8}\.[0-9]{4}\.gz", file_prefix="rcc24_")
    dl_latest_file(base_url=f"https://data.ris.ripe.net/rrc25/{ripe_date_str}/", file_regex=r"bview.[0-9]{8}\.[0-9]{4}\.gz", file_prefix="rcc25_")
    dl_latest_file(base_url=f"http://archive.routeviews.org/bgpdata/{ripe_date_str}/RIBS/", file_regex=r"rib.[0-9]{8}\.[0-9]{4}\.bz2")
    # AS Relationships
    dl_latest_file(base_url="https://data.caida.org/datasets/as-relationships/serial-2/", file_regex=r"[0-9]{8}\.as-rel2\.txt\.bz2", auth=("jens.friess@tu-darmstadt", "CaidaAlwaysIsDaAnswer"))
    # Prefix2AS
    dl_latest_file(base_url=f"https://publicdata.caida.org/datasets/routing/routeviews-prefix2as/{caida_date_str}/", file_regex=r"routeviews-rv2-[0-9]{8}-1200\.pfx2as\.gz")


def dl_latest_file(base_url: str, file_regex: str, file_prefix: str = "", auth: Tuple[str, str] = None):
    latest_file = find_latest_file(dir_url=base_url, file_regex=file_regex)
    dl_file(url=base_url + latest_file, filename=file_prefix + latest_file, auth=auth)


def dl_file(url: str, filename: str, auth: Tuple[str, str] = None):
    print(f"downloading {url} into {filename}")
    write_bytes(filename, requests.get(url, auth=auth).content)


def find_latest_file(dir_url: str, file_regex: str) -> str:
    html = requests.get(dir_url)
    return sorted(re.findall(file_regex, html.text))[-1]


def write_bytes(filename: str, content: bytes):
    with open(filename, "wb") as f:
        f.write(content)


def parse_args() -> Namespace:
    parser = ArgumentParser(description="Downloads latest available CAIDA AS Relationship and Prefix2AS datasets.")
    return parser.parse_args()


if __name__ == '__main__':
    parse_args()
    main()

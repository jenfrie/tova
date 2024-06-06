#!/usr/bin/env python3
import sys
from multiprocessing.pool import ThreadPool
from typing import Tuple

import requests
from requests import Timeout, ConnectionError
from tqdm import tqdm
from urllib3.exceptions import LocationParseError


def query(domain: str) -> Tuple[str, bool]:
    try:
        requests.get(f"http://{domain}/robots.txt", timeout=10, allow_redirects=False)
        return domain, True
    except (Timeout, ConnectionError, LocationParseError):
        return domain, False


# pipe in domains list
domains = [line.split(',')[-1].strip() if ',' in line else line.strip() for line in sys.stdin]

with ThreadPool(30) as pool:
    results = list(tqdm((pool.imap(query, domains)), total=len(domains)))

for domain, reachable in results:
    if reachable:
        # redirect stdout to file
        print(domain)

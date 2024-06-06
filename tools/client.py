#!/usr/bin/env python3
import sys
from math import ceil
from multiprocessing.pool import Pool, ThreadPool
from time import sleep

import requests
import urllib3
from requests import Timeout, ConnectionError
from tqdm import tqdm


server = "localhost"

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def query(url: str):
    attempt = 1
    while attempt < 3:
        try:
            return requests.get(url, timeout=60, verify=False).status_code
        except Timeout:
            sleep(2**attempt)
        except ConnectionError as e:
            if "Connection aborted." in str(e):
                sleep(2**attempt)
        attempt += 1
    return "failed"


# pipe in domains list
urls = [f"https://{server}/http/{line.split(',')[-1].strip() if ',' in line else line.strip()}/robots.txt" for line in sys.stdin]
n = 150
chunksize = min(max(10, ceil(0.01 * len(urls) / n)), 200)

with ThreadPool(n) as pool:
    res = list(tqdm(pool.imap(query, urls, chunksize=chunksize), total=len(urls), leave=True))

print(f"total vals: {len(res)}")
print(f"completed: {sum(1 for r in res if r == 200)}")
print(f"failed: {sum(1 for r in res if r == 'failed')}")

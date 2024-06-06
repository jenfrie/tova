#!/usr/bin/env python3
import json
import sys
from threading import Thread
from time import time

import requests
import urllib3

session = requests.Session()
session.headers.update({"User-Agent": "CTQueueLoader"})
session.verify = False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
server_domain = "localhost"


def send_to_queue(domain: str):
    try:
        session.get(f"https://{server_domain}/http/{domain}/robots.txt", verify=False, timeout=30)
    except:
        pass


def main():
    for line in sys.stdin:
        if "O=Let's Encrypt" in line and "PrecertLogEntry" in line:
            data = json.loads(line.strip())
            domains = {domain.lstrip("*.") for domain in data["data"]["leaf_cert"]["all_domains"]}
            for domain in domains:
                Thread(target=send_to_queue, args=(domain,), daemon=True).start()
                print(data["data"]["leaf_cert"]["not_before"], domain)


if __name__ == '__main__':
    print(f"start: {time()}")
    try:
        main()
    except KeyboardInterrupt:
        print(f"end: {time()}")

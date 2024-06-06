import json
import os
import random
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from ipaddress import IPv4Network
from time import time, sleep
from typing import Union, Set

import requests
from UltraDict import UltraDict
from flask import Flask
from stem import StreamStatus, SocketError
from stem.control import Controller
from stem.response.events import CircuitEvent

from env import REQUEST_TIMEOUT, VAL_N, VAL_K, PREFIX_LEN, CIRCUIT_TTL

app = Flask(__name__)


@app.route("/http/<domain>/<path:challenge>")
def http_acme_proxy(domain: str, challenge: str):
    return acme_proxy("http", domain, challenge)


@app.route("/https/<domain>/<path:challenge>")
def https_acme_proxy(domain: str, challenge: str):
    return acme_proxy("https", domain, challenge)


def acme_proxy(protocol: str, domain: str, challenge: str):
    req_start = time()

    votes = {}
    current_circuits = set()
    stream_exits, target_exits = {}, {}
    url = f"{protocol}://{domain}/{challenge}"
    futures = []

    while True:
        n_threads = VAL_K - max_votes(votes)
        with ThreadPoolExecutor(n_threads) as pool:
            futures += [pool.submit(get, url) for _ in range(n_threads)]

            while len(target_exits) < n_threads:
                try:
                    for stream in ctrl.get_streams():
                        if stream.status == StreamStatus.NEW and stream.target_address == domain:
                            while True:
                                try:
                                    circ = random.choice(ctrl.get_circuits())
                                    if circ.id not in current_circuits and created.get(circ.id, 0) + CIRCUIT_TTL < time():
                                        ctrl.attach_stream(stream.id, circ.id)
                                        stream_exits[stream.id] = exit_ip_of(circ)
                                        current_circuits.add(circ.id)
                                        if not created.get(circ.id):
                                            created[circ.id] = time()
                                        break
                                except:
                                    pass

                        elif stream.status == StreamStatus.SUCCEEDED and stream_exits.get(stream.id):
                            target_exits[stream_exits[stream.id]] = stream.target_address
                except:
                    sleep(0.5)

            done = []
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=REQUEST_TIMEOUT + 5)
                    votes[result] = votes.setdefault(result, 0) + 1
                    done.append(future)
                except TimeoutError:
                    pass
            futures = [future for future in futures if future not in done]

        if max_votes(votes) >= VAL_K:
            output, vote = sorted(votes.items(), key=lambda x: x[1])[-1]
            break
        elif sum(votes.values()) >= VAL_N:
            output, vote = "ERROR", max_votes(votes)
            break

    log(req_start=req_start, req_end=time(), ok="ERR" not in output, domain=domain, exit_target_pairs=list(target_exits.items()))
    return output


def subnet_of(ip: str) -> IPv4Network:
    return IPv4Network(f"{ip}/{PREFIX_LEN}", strict=False)


def subnets_in_use() -> Set[IPv4Network]:
    return {subnet_of(exit_ip_of(circ)) for circ in ctrl.get_circuits()}


def exit_ip_of(circ: Union[CircuitEvent, str]) -> str:
    try:
        if isinstance(circ, str):
            circ = ctrl.get_circuit(circ)
        return ctrl.get_network_status(circ.path[-1][0]).address
    except (IndexError, ValueError):
        return "0.0.0.0"


def max_votes(votes: dict) -> int:
    try:
        return max(votes.values())
    except ValueError:
        return 0


def get(url: str) -> str:
    try:
        r = sess.get(url, allow_redirects=False, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        return r.text
    except Exception as e:
        #log(error=str(e.__class__), url=url)
        return f"ERR: {e.__class__}"


def log(**data):
    with open(f"/app/logs/app-{PID}.log", "a") as f:
        data = {k: list(v) if isinstance(v, set) else v for k, v in data.items()}
        f.write(json.dumps(data) + "\n")


sess = requests.session()
sess.proxies = {"http": "socks5h://127.0.0.1:9050",
                "https": "socks5h://127.0.0.1:9050"}

while True:
    try:
        ctrl = Controller.from_port()
        break
    except SocketError:
        sleep(2)
ctrl.authenticate()

created = UltraDict(name="circuit_creation")
PID = os.getpid()


if __name__ == '__main__':
    app.run()

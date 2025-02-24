import json
import os
import random
import re
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from ipaddress import IPv4Network
from time import time, sleep
from typing import Union, Set

import requests
from UltraDict import UltraDict
from flask import Flask
from stem import StreamStatus, SocketError, InvalidArguments, InvalidRequest
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
    results = []
    current_circuits = set()
    stream_exits, target_exits = {}, {}
    url = f"{protocol}://{domain}/{challenge}"
    futures = []

    while True:
        n_threads = VAL_K - max_votes(votes)
        with ThreadPoolExecutor(n_threads) as pool:
            #futures += [pool.submit(get, url) for _ in range(n_threads)]
            for _ in range(n_threads):
                future = pool.submit(get, url)
                stream_id = 0
                while stream_id == 0:
                    sleep(0.1)
                    stream_ids = {stream.id for stream in ctrl.get_streams() if stream.status == StreamStatus.NEW and stream.target_address == domain}
                    new_stream_ids = sorted(stream_ids - {stream_id for stream_id, _ in futures})
                    stream_id = new_stream_ids[-1] if len(new_stream_ids) > 0 else 0
                futures.append((stream_id, future))

            t = time()
            while len(target_exits) < n_threads and time() < t + REQUEST_TIMEOUT:
                try:
                    for stream in ctrl.get_streams():
                        if stream.status == StreamStatus.NEW and stream.target_address == domain:
                            while True:
                                available_circs = [circ for circ in ctrl.get_circuits() if circ.status == "BUILT" and len(circ.path) > 1 and circ.id not in current_circuits and created.get(circ.id, 0) + CIRCUIT_TTL > time()]
                                try:
                                    circ = random.choice(available_circs)
                                    ctrl.attach_stream(stream.id, circ.id)
                                    stream_exits[stream.id] = exit_ip_of(circ)
                                    current_circuits.add(circ.id)
                                    if not created.get(circ.id):
                                        created[circ.id] = time()
                                    break

                                except (InvalidArguments, InvalidRequest):
                                    n_threads -= 1
                                    break
                                except IndexError:
                                    sleep(0.5)
                                except:
                                    sleep(0.1)

                        elif any(stream.status == status for status in [StreamStatus.SUCCEEDED, StreamStatus.FAILED, StreamStatus.DETACHED, StreamStatus.CLOSED]) and stream_exits.get(stream.id):
                            target_exits[stream_exits[stream.id]] = stream.target_address
                            if stream.status == StreamStatus.DETACHED:
                                ctrl.close_stream(stream.id)
                except:
                    sleep(0.1)

            while len(futures) > 0:
                done_futures = [(stream_id, future) for stream_id, future in futures if future.done()]
                for stream_id, future in done_futures:
                    try:
                        result = brev(future.result(timeout=1))
                        futures.remove((stream_id, future))
                        results.append((stream_exits[stream_id], target_exits.get(stream_exits[stream_id]), result))
                        votes[result] = votes.setdefault(result, 0) + 1
                    except (TimeoutError, KeyError):
                        pass

        if max_votes(votes) >= VAL_K:
            output, vote = sorted(votes.items(), key=lambda x: x[1])[-1]
            break
        elif sum(votes.values()) >= VAL_N:
            output, vote = "ERROR", max_votes(votes)
            break

    log(req_start=req_start, req_end=time(), ok="ERR" not in output, domain=domain, results=results)
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
        return f"ERR: {e.__class__}"


def log(**data):
    with open(f"/app/logs/app-{PID}.log", "a") as f:
        data = {k: list(v) if isinstance(v, set) else v for k, v in data.items()}
        f.write(json.dumps(data) + "\n")


def brev(s: str, max_len: int = 100) -> str:
    return f"{s[:int(max_len / 2)]} ..[{len(s) - max_len}].. {s[-int(max_len / 2):]}" if len(s) > max_len + 9 else s


def is_ip(s: str) -> bool:
    return re.match("[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}", s) is not None


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

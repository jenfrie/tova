import json
import random
from ipaddress import IPv4Network
from math import ceil
from time import sleep, time
from typing import Set, List, Tuple, Union, Optional

import requests
from UltraDict import UltraDict
from requests import ConnectionError
from stem import SocketError, InvalidArguments, Flag, InvalidRequest, CircuitExtensionFailed, DescriptorUnavailable
from stem import Timeout
from stem.control import Controller
from stem.descriptor.router_status_entry import RouterStatusEntry
from stem.response.events import CircuitEvent

from env import CIRCUIT_TTL, PREFIX_LEN, N_CIRCUITS, VAL_K, BUILD_INTERVAL

created = UltraDict({}, name="circuit_creation", buffer_size=8192, auto_unlink=True)
subnets = set()
host_ip = ""

while True:
    try:
        ctrl = Controller.from_port()
        break
    except SocketError:
        sleep(2)
ctrl.authenticate()


def renew_circuits(guards: List[RouterStatusEntry], exits: List[RouterStatusEntry]):
    active = {circ.id for circ in ctrl.get_circuits() if circ.status == "BUILT"}
    expired = get_expired_circuits(active)
    to_build = max(0, min(N_CIRCUITS, N_CIRCUITS - len(active) + len(expired)))
    log(active=len(active), expired=len(expired), to_build=to_build)

    if to_build > 0:
        new_guards, new_exits = get_relays()
        guards = new_guards if new_guards else guards
        exits = new_exits if new_exits else exits
        log(guards=len(guards), exits=len(exits))

        build_circuits(guards, exits, n=to_build)

    if expired:
        closed = expire_circuits(expired)
        log(closed=closed)

    return guards, exits


def expire_circuits(circuits: List[str]) -> int:
    closed = 0
    for circ_id in circuits:
        if circ_id not in open_streams():
            try:
                subnets.remove(subnet_of(exit_ip_of(circ_id)))
            except KeyError:
                pass
            try:
                ctrl.close_circuit(circ_id)
            except InvalidArguments:
                pass
            del created[circ_id]
            closed += 1
    return closed


def get_expired_circuits(active_circuits: Optional[List[str]] or None) -> List[str]:
    active_circuits = active_circuits or {circ.id for circ in ctrl.get_circuits()}
    return [circ_id for circ_id, timestamp in created.items() if time() > timestamp + CIRCUIT_TTL or circ_id not in active_circuits]


def open_streams() -> Set[str]:
    return {stream.circ_id for stream in ctrl.get_streams()}


def get_relays() -> Tuple[List[RouterStatusEntry], List[RouterStatusEntry]]:
    for _ in range(3):
        try:
            relays = set(ctrl.get_network_statuses())

            exits = {relay for relay in relays if Flag.EXIT in relay.flags and Flag.BADEXIT not in relay.flags and Flag.RUNNING in relay.flags}
            guards = {relay for relay in relays - exits if Flag.GUARD in relay.flags and Flag.FAST in relay.flags and Flag.RUNNING in relay.flags}
            return list(guards), list(exits)

        except DescriptorUnavailable:
            log(error="failed to retrieve relays")
            sleep(1)
    return [], []


def build_circuits(guards: List[RouterStatusEntry], exits: List[RouterStatusEntry], n: int):
    guard_weights = weight_guards(guards)

    paths = set()
    while len(paths) < n and len(exits) > 0:
        exit = random.choice(exits)
        subnet = subnet_of(exit.address)
        if subnet not in subnets:
            guard = random.choices(guards, weights=guard_weights, k=1)[0]
            paths.add((guard.fingerprint, exit.fingerprint))
            subnets.add(subnet)
        exits.remove(exit)

    for path in paths:
        build_circuit(list(path))


def build_circuit(path: List[str]) -> int:
    try:
        circ_id = ctrl.new_circuit(path, await_build=False)
        created[circ_id] = time()
        return circ_id
    except (InvalidRequest, CircuitExtensionFailed, Timeout):
        return -1


def weight_guards(guards: List[RouterStatusEntry]) -> List[int]:
    if host_ip:
        return [guard.bandwidth * ceil(network_overlap(host_ip, guard.address)) for guard in guards]
    else:
        return [guard.bandwidth for guard in guards]


def network_overlap(ip1: str, ip2: str) -> int:
    bin_ip1, bin_ip2 = bin_ip(ip1), bin_ip(ip2)
    i = 0
    while bin_ip1[i] == bin_ip2[i]:
        i += 1
    return max(1, i)


def bin_ip(ip: str) -> str:
    return ''.join(format(int(octet), '08b') for octet in ip.split('.'))


def subnet_of(ip: str) -> IPv4Network:
    return IPv4Network(f"{ip}/{PREFIX_LEN}", strict=False)


def subnets_in_use() -> Set[IPv4Network]:
    return {subnet_of(exit_ip_of(circ)) for circ in ctrl.get_circuits()}


def exit_ip_of(circ: Union[CircuitEvent, str]) -> str:
    try:
        if isinstance(circ, str):
            circ = ctrl.get_circuit(circ)
        return ctrl.get_network_status(circ.path[-1][0]).address
    except (IndexError, ValueError, DescriptorUnavailable):
        return "0.0.0.0"


def get_ip() -> str:
    for attempt in range(1, 4):
        try:
            return requests.get("https://ipv4.icanhazip.com/").text.strip()
        except ConnectionError:
            sleep(2**attempt)


def log(**data):
    with open("/app/logs/circus.log", "a") as f:
        data = {k: list(v) if isinstance(v, set) else v for k, v in data.items()}
        f.write(json.dumps(data) + "\n")


def main():
    host_ip = get_ip()
    log(ip=host_ip if host_ip else None)

    log(to_build=N_CIRCUITS)
    guards, exits = set(), set()
    while not exits and not guards:
        guards, exits = get_relays()
        sleep(2)
    log(guards=len(guards), exits=len(exits))

    for _ in range(0, N_CIRCUITS, VAL_K):
        build_circuits(guards, exits, VAL_K)
        sleep(BUILD_INTERVAL)

    while True:
        guards, exits = renew_circuits(guards, exits)
        sleep(BUILD_INTERVAL)


if __name__ == '__main__':
    main()

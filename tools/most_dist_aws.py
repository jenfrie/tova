#!/usr/bin/env python3
from ipaddress import IPv4Network

import requests
from tqdm import tqdm


def overlap(net1: IPv4Network, net2: IPv4Network) -> int:
    return 32 - (int(net1.network_address) ^ int(net2.network_address)).bit_length()


N = 30

aws_ip_ranges = requests.get("https://ip-ranges.amazonaws.com/ip-ranges.json").json()
ec2_nets = [IPv4Network(net["ip_prefix"]) for net in aws_ip_ranges["prefixes"] if net["service"] == "EC2"]

LE_main_net = IPv4Network("23.178.112.0/24")
selected = [LE_main_net]

for _ in tqdm(list(range(1, N))):
    overlaps = {new_net: [overlap(new_net, net) for net in selected] for new_net in ec2_nets}
    new_net = sorted(overlaps.keys(), key=lambda x: sum(overlaps[x]) / len(overlaps[x]))[0]
    selected.append(new_net)
    ec2_nets.remove(new_net)

print("\n".join([str(next(net.hosts())) for net in selected]))
print([str(next(net.hosts())) for net in selected])

#!/usr/bin/env python3
from stem.control import Controller


def main():
    with Controller.from_port() as ctrl:
        ctrl.authenticate()

        for circuit in ctrl.get_circuits():
            if circuit.purpose != "GENERAL" and circuit.purpose != "CONFLUX_LINKED":
                color = "\033[90m"
            elif circuit.status == "BUILT":
                color = "\033[32m"
            elif circuit.status == "LAUNCHED" or circuit.status == "EXTENDED":
                color = "\033[33m"
            elif circuit.status == "FAILED" or circuit.status == "CLOSED":
                color = "\033[31m"

            print(color + circuit.purpose + "\t" + "\t->\t".join(ctrl.get_network_status(relay[0]).address for relay in circuit.path) + "\033[0m")


if __name__ == '__main__':
    main()

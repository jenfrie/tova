import random
from concurrent.futures import ThreadPoolExecutor
from time import sleep, time

import requests
from stem import Flag, Timeout, CircuitExtensionFailed, InvalidRequest, InvalidArguments
from stem.control import Controller

print("setting up")
ctrl = Controller.from_port()
ctrl.authenticate()

print("closing existing circuits")
for circ in ctrl.get_circuits():
    ctrl.close_circuit(circ.id)

relays = list(ctrl.get_network_statuses())
exits = [r for r in relays if Flag.EXIT in r.flags and Flag.BADEXIT not in r.flags]
guards = [r for r in relays if Flag.GUARD in r.flags]
futures = {}
stream_ids = {}
ips = {}

subs = [f"{sub}.toval.online" for sub in "abcdefgh"]


sess = requests.session()
sess.proxies = {"http": "socks5h://127.0.0.1:9050",
                "https": "socks5h://127.0.0.1:9050"}


def get(domain: str):
    print(f"requesting {domain}", flush=True)
    try:
        sess.get(f"http://{domain}/", allow_redirects=False, timeout=10)
        return True
    except Exception as e:
        # print(f"request err: {str(e)}")
        return False


with ThreadPoolExecutor() as pool:
    for i, exit in enumerate(exits):
        for attempt in range(3):
            circ_id = 0
            print(i, exit.address, f"attempt {attempt}", flush=True)
            guard = random.choice(guards)
            try:
                circ_id = ctrl.new_circuit([guard.fingerprint, exit.fingerprint], await_build=True, timeout=30)
                break
            except (InvalidRequest, CircuitExtensionFailed, Timeout) as e:
                pass

        if circ_id:
            print(i, exit.address, f"circ built ({circ_id})", flush=True)
            futures[circ_id] = pool.submit(get, subs[i % len(subs)])
            ips[circ_id] = (i, exit.address)
            for _ in range(3):
                sleep(2)
                for stream in ctrl.get_streams():
                    if stream.id not in stream_ids.values():
                        ctrl.attach_stream(stream.id, circ_id)
                        stream_ids[circ_id] = stream.id
                        print(i, exit.address, f"stream attached ({stream.id}) at {time()}", flush=True)
                        break
                if stream_ids.get(circ_id):
                    break

        done = []
        for circ_id, future in futures.items():
            if future.done():
                i, ip = ips[circ_id]
                print(i, ip, f"stream finished at {time()}", flush=True)
                try:
                    ctrl.close_circuit(circ_id)
                except InvalidArguments:
                    pass
                done.append(circ_id)

        for circ_id in done:
            try:
                del futures[circ_id]
            except KeyError:
                pass
            try:
                del stream_ids[circ_id]
            except KeyError:
                pass
            try:
                del ips[circ_id]
            except KeyError:
                pass

#!/usr/bin/env python3
import functools

from stem.control import EventType, Controller

def main():
  print("Tracking requests for tor exits. Press 'enter' to end.")
  print("")

  with Controller.from_port() as controller:
    controller.authenticate()

    stream_listener = functools.partial(stream_event, controller)
    controller.add_event_listener(stream_listener, EventType.STREAM)

    input()  # wait for user to press enter


def stream_event(controller, event):
  if event.circ_id:
    circ = controller.get_circuit(event.circ_id)
    print(f"{event.status}\t{event.target}\t{controller.get_network_status(circ.path[-1][0]).address}")


if __name__ == '__main__':
  main()

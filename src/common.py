import os
import pickle
import socket
from urllib.parse import urlparse

from landscape import CLIENT_API
from landscape.client.diff import diff
from landscape.client.exchange import exchange_messages
from landscape.lib.process import ProcessInformation

PROCESS_INFO = ProcessInformation()


def get_processes():
    ps = {}
    pis = (p for p in PROCESS_INFO.get_all_process_info() if p["state"] != b"X")

    for pi in pis:
        ps[pi["pid"]] = pi

    return ps


def get_changes(process_diff: tuple):
    creates, updates, deletes = process_diff
    return {
        k + "-processes": list(v.values())
        for k, v in (("add", creates), ("update", updates), ("kill", deletes))
        if v
    }


def send_messages(messages, sequence, exchange_token, computer_id, host):
    payload = {
        "client-api": CLIENT_API,
        "sequence": sequence,
        "next-expected-sequence": 1,
        "messages": messages,
    }

    response = exchange_messages(
        payload,
        host + "/message-system",
        computer_id=computer_id,
        exchange_token=exchange_token,
    )

    return response.next_exchange_token, response.next_expected_sequence


def generate_message(prev_processes: dict):
    message: dict[str, str | list] = {"type": "active-process-info"}
    processes = get_processes()
    process_diff = diff(prev_processes, processes)
    changes = get_changes(process_diff)

    if changes:
        message.update(changes)
        return message, prev_processes

    return None, prev_processes


def get_params(host: str):
    """Gets startup params from the locust buddy."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        hostname = urlparse(host).hostname
        port = os.getenv("LANDSCAPE_LOCUST_BUDDY_PORT", "9999")
        s.connect((hostname, port))
        pickled = s.recv(1024)
        secure_id, exchange_token, sequence, insecure_id = pickle.loads(pickled)

    return exchange_token, sequence, secure_id.decode(), insecure_id

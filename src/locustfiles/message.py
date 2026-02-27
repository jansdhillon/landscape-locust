import os
import pickle
import socket
import ssl
import tempfile
import time
from urllib.parse import urlparse

from landscape import CLIENT_API
from landscape.client.diff import diff
from landscape.client.exchange import exchange_messages
from landscape.lib.process import ProcessInformation
from locust import FastHttpUser, tag, task
from locust.env import Environment
from locust.event import EventHook

PROCESS_INFO = ProcessInformation()
_cainfo_cache: dict[str, str | None] = {}


def get_cainfo(host: str) -> str | None:
    """Fetch the server's certificate once and cache it as a temp file for cainfo."""
    if host in _cainfo_cache:
        return _cainfo_cache[host]

    parsed = urlparse(host)
    if parsed.scheme != "https":
        _cainfo_cache[host] = None
        return None
    hostname = parsed.hostname
    port = parsed.port or 443
    try:
        cert_pem = ssl.get_server_certificate((hostname, port))
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=".pem", mode="w", prefix="landscape-locust-cert-"
        ) as f:
            f.write(cert_pem)
            _cainfo_cache[host] = f.name

    except Exception:
        _cainfo_cache[host] = None
        return None

    return _cainfo_cache[host]


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


def send_messages(
    messages: dict,
    sequence: int,
    exchange_token: str,
    computer_id: int,
    host: str,
    cainfo: str | None = None,
):
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
        cainfo=cainfo,
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
        hostname = os.getenv(
            "LANDSCAPE_LOCUST_EXCHANGE_SERVER_HOST", "landscape-locust-exchange"
        )
        port = int(os.getenv("LANDSCAPE_LOCUST_EXCHANGE_SERVER_PORT", "9999"))
        s.connect((hostname, port))
        pickled = s.recv(1024)
        secure_id, exchange_token, sequence, insecure_id = pickle.loads(pickled)

    return exchange_token, sequence, secure_id.decode(), insecure_id


class MessageSystemClient:
    """A locust client for performing Landscape message exchanges."""

    def __init__(
        self, host: str, request_event: EventHook, cainfo: str | None = None
    ) -> None:
        self._host = host
        self._request_event = request_event
        self._cainfo = cainfo

    def send_messages(self, messages: dict, sequence: int, token: str, cid: int):
        request_meta = {
            "request_type": "landscape-message",
            "name": "message-exchange",
            "start_time": time.time(),
            "response_length": 0,
            "response": None,
            "context": {},
            "exception": None,
        }
        start_perf_counter = time.perf_counter()
        try:
            result = send_messages(
                messages, sequence, token, cid, self._host, self._cainfo
            )
        except Exception as e:
            request_meta["exception"] = e
            result = None
        request_meta["response_time"] = (
            time.perf_counter() - start_perf_counter
        ) * 1000
        self._request_event.fire(**request_meta)
        return result


class MessageSystemUser(FastHttpUser):
    insecure = True

    def __init__(self, environment: Environment) -> None:
        super().__init__(environment)

        if not self.host:
            return

        cainfo = get_cainfo(self.host)
        self._message_system_client = MessageSystemClient(
            self.host, environment.events.request, cainfo
        )

    def wait_time(self):
        """override default wait time."""
        return 30

    def on_start(self):
        if not self.host:
            return

        self._next_exchange_token, self._sequence, self._id, self._insecure_id = (
            get_params(self.host)
        )

    @tag("message-traffic")
    @task
    def spam_active_processes(self):
        self._prev_processes = {}
        messages = []
        max_messages = int(
            os.getenv("LANDSCAPE_LOCUST_MESSAGE_SERVER_MAX_MESSAGES", "10")
        )
        for _ in range(max_messages):
            message, self._prev_processes = generate_message(self._prev_processes)
            if message:
                messages.append(message)

        result = self._message_system_client.send_messages(
            messages,
            self._sequence,
            self._next_exchange_token,
            self._id,
        )

        if result is None:
            return

        self._next_exchange_token, self._sequence = result

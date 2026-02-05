import pickle
import socket
import time
from urllib.parse import urlparse

from constants import BUDDY_PORT, MAX_MESSAGE_COUNT
from locust import FastHttpUser, tag, task
from spam_processes import generate_message, send_messages


class MessageSystemClient:
    """A locust client for performing Landscape message exchanges."""

    def __init__(self, host, request_event):
        self._host = host
        self._request_event = request_event

    def send_messages(self, messages, sequence, token, cid):
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
            result = send_messages(messages, sequence, token, cid, self._host)
        except Exception as e:
            request_meta["exception"] = e
            result = None
        request_meta["response_time"] = (
            time.perf_counter() - start_perf_counter
        ) * 1000
        self._request_event.fire(**request_meta)
        return result


def get_params(host):
    """Gets startup params from the locust buddy."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        hostparts = urlparse(host)
        hostname = hostparts.hostname

        s.connect((hostname, BUDDY_PORT))
        pickled = s.recv(1024)
        secure_id, exchange_token, sequence, insecure_id = pickle.loads(pickled)

    return exchange_token, sequence, secure_id.decode(), insecure_id


class MessageSystemUser(FastHttpUser):
    def __init__(self, environment):
        super().__init__(environment)

        self._message_system_client = MessageSystemClient(
            self.host, environment.events.request
        )

    def wait_time(self):
        """override default wait time."""
        return 30

    def on_start(self):
        self._next_exchange_token, self._sequence, self._id, self._insecure_id = (
            get_params(self.host)
        )

    @tag("message-traffic")
    @task
    def spam_active_processes(self):
        self._prev_processes = {}
        messages = []
        for _ in range(MAX_MESSAGE_COUNT):
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

    @tag("ping-traffic")
    @task
    def spam_pings(self):
        self.wait()
        self.client.post(self.host + "/ping", data={"insecure_id": self._insecure_id})

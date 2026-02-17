import os
import time

from locust import FastHttpUser, tag, task
from locust.env import Environment
from locust.event import EventHook

from src.common import generate_message, get_params, send_messages


class MessageSystemClient:
    """A locust client for performing Landscape message exchanges."""

    def __init__(self, host: str, request_event: EventHook) -> None:
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


class MessageSystemUser(FastHttpUser):
    def __init__(self, environment: Environment) -> None:
        super().__init__(environment)

        if not self.host:
            return

        self._message_system_client = MessageSystemClient(
            self.host, environment.events.request
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

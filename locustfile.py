import pickle
import socket
import time

from locust import User, task
from spam_processes import generate_message, send_messages

MAX_MESSAGE_COUNT = 1
BUDDY = ('10.149.172.190', 9999)


class MessageSystemClient:
    """Fancy."""

    def __init__(self, host, request_event):
        self._host = host
        self._request_event = request_event

    def send_messages(self, messages, sequence, token, cid):
        request_meta = {
            'request_type': 'landscape-message',
            'name': 'message-exchange',
            'start_time': time.time(),
            'response_length': 0,
            'response': None,
            'context': {},
            'exception': None,
        }
        start_perf_counter = time.perf_counter()
        try:
            result = send_messages(messages, sequence, token, cid, self._host)
        except Exception as e:
            request_meta['exception'] = e
            result = None
        request_meta['response_time'] = (time.perf_counter() - start_perf_counter) * 1000
        self._request_event.fire(**request_meta)
        return result


def get_params():
    """Gets startup params from the locust buddy."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(BUDDY)
        pickled = s.recv(1024)
        secure_id, exchange_token, sequence = pickle.loads(pickled)

    return exchange_token, sequence, secure_id.decode()

class MessageSystemUser(User):

    def __init__(self, environment):
        super().__init__(environment)
        self.client = MessageSystemClient(self.host, environment.events.request)

    def on_start(self):
        self._next_exchange_token, self._sequence, self._id = get_params()

    @task
    def spam_active_processes(self):
        self._prev_processes = {}
        messages = []
        for _ in range(MAX_MESSAGE_COUNT):
            message, self._prev_processes = generate_message(self._prev_processes)
            if message:
                messages.append(message)

        result = self.client.send_messages(
            messages,
            self._sequence,
            self._next_exchange_token,
            self._id,
        )

        if result is None:
            return

        self._next_exchange_token, self._sequence = result

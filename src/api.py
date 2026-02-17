from locust import FastHttpUser, tag, task
from locust.event import EventHook


class APIUser(FastHttpUser):
    def __init__(self) -> None:
        super().__init__(self.environment)

    @tag("api-traffic")
    @task
    def spam_api(self, endpoint="/computers") -> None:
        self.client.get(self.host + endpoint)

from locust import tag, task
from locustfiles.message import MessageSystemUser


class PingserverUser(MessageSystemUser):
    @tag("ping-traffic")
    @task
    def spam_pings(self):
        self.wait()
        self.client.post(f"{self.host}/ping", data={"insecure_id": self._insecure_id})

from locust import tag, task

from message import MessageSystemUser


class PingserverUser(MessageSystemUser):
    insecure = True

    @tag("ping-traffic")
    @task
    def spam_pings(self):
        self.wait()
        self.client.post(f"{self.host}/ping", data={"insecure_id": self._insecure_id})

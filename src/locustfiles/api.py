from locust import FastHttpUser, tag, task


class APIUser(FastHttpUser):
    @tag("api-traffic")
    @task
    def spam_api(self, endpoint: str = "/computers") -> None:
        self.client.get(self.host + endpoint)

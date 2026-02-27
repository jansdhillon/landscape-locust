import logging
import os

from locust import FastHttpUser, tag, task

logger = logging.getLogger(__name__)


class APIUser(FastHttpUser):
    insecure = True

    def on_start(self) -> None:
        email = os.getenv("LANDSCAPE_LOCUST_EMAIL")
        password = os.getenv("LANDSCAPE_LOCUST_PASSWORD")
        with self.client.post(
            "/api/login",
            json={"email": email, "password": password},
            catch_response=True,
        ) as response:
            try:
                data = response.json()
            except Exception:
                response.failure(
                    f"Login returned non-JSON (status {response.status_code}): {response.text[:200]!r}"
                )
                self._jwt = None
                return
            self._jwt = data.get("token")
            if self._jwt:
                response.success()
                logger.info("Logged in as %s", email)
            else:
                response.failure(f"No token in login response: {data}")

    @tag("api-traffic")
    @task
    def spam_api(self, endpoint: str = "/api/v2/computers") -> None:
        if not self._jwt:
            return
        self.client.get(
            endpoint,
            headers={"Authorization": f"Bearer {self._jwt}"},
        )

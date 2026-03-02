import logging
import os

import gevent.lock
from locust import FastHttpUser, tag, task

logger = logging.getLogger(__name__)


class APIUser(FastHttpUser):
    insecure = True
    _jwt: str | None = None
    _login_lock = gevent.lock.Semaphore()

    def on_start(self) -> None:
        if APIUser._jwt:
            self._jwt = APIUser._jwt
            return

        with APIUser._login_lock:
            if APIUser._jwt:
                self._jwt = APIUser._jwt
                return

            access_key = os.getenv("LANDSCAPE_LOCUST_ACCESS_KEY")
            secret_key = os.getenv("LANDSCAPE_LOCUST_SECRET_KEY")

            if access_key and secret_key:
                endpoint = "/api/login/access-key"
                payload = {"access_key": access_key, "secret_key": secret_key}
                identifier = access_key
            else:
                endpoint = "/api/login"
                payload = {
                    "email": os.getenv("LANDSCAPE_LOCUST_EMAIL"),
                    "password": os.getenv("LANDSCAPE_LOCUST_PASSWORD"),
                }
                identifier = payload["email"]

            with self.client.post(
                endpoint, json=payload, catch_response=True
            ) as response:
                try:
                    data = response.json()
                except Exception:
                    response.failure(
                        f"Login returned non-JSON (status {response.status_code}): {response.text[:200]!r}"
                    )
                    return
                APIUser._jwt = data.get("token")
                if APIUser._jwt:
                    response.success()
                    logger.info("Logged in as %s", identifier)
                else:
                    response.failure(f"No token in login response: {data}")
            self._jwt = APIUser._jwt

    @tag("api-traffic")
    @task
    def spam_api(self, endpoint: str = "/api/computers") -> None:
        if not self._jwt:
            return
        with self.client.get(
            endpoint,
            headers={"Authorization": f"Bearer {self._jwt}"},
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(
                    f"GET {endpoint} returned {response.status_code}: {response.text[:200]!r}"
                )

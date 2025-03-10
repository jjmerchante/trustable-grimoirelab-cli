import logging
import time

import requests


MAX_RETRIES = 5


class GrimoireLabClient:
    """
    Client to interact with GrimoireLab API.

    :param url: GrimoireLab API URL.
    :param user: Username to use when authentication is required.
    :param password: Password to use when authentication is required.
    """

    def __init__(self, url: str, user: str = None, password: str = None):
        self.url = url
        self.user = user
        self.password = password
        self.session = None
        self._token = None
        self._refresh_token = None

    def connect(self):
        """Establish a connection to the server, and create a token"""

        self.session = requests.Session()
        if not (self.user and self.password):
            return

        credentials = {"username": self.user, "password": self.password}
        res = self.post("token/", json=credentials)
        res.raise_for_status()
        data = res.json()

        self._token = data.get("access")
        self._refresh_token = data.get("refresh")

        self.session.headers.update({"Authorization": f"Bearer {self._token}"})

    def _reconnect(self):
        """Reconnect to the server using a new Session and the current token"""

        logging.debug("Server closed the connection. Reconnecting to the server.")

        self.session = requests.Session()
        if self._token:
            self.session.headers.update({"Authorization": f"Bearer {self._token}"})

    def get(self, uri: str, *args, **kwargs) -> requests.Response:
        """
        Make a GET request to the GrimoireLab API.
        Check if the token is still valid, if not, refresh it.

        :param uri: URI to request.
        """
        return self._make_request("get", uri, *args, **kwargs)

    def post(self, uri: str, *args, **kwargs) -> requests.Response:
        """
        Make a POST request to the GrimoireLab API.
        Check if the token is still valid, if not, refresh it.

        :param uri: URI to request.
        """
        return self._make_request("post", uri, *args, **kwargs)

    def _make_request(self, method: str, uri: str, *args, **kwargs) -> requests.Response:
        """
        Make a request to the GrimoireLab API with retry and exponential backoff.
        If the session is invalid or the token is expired, it attempts to reconnect and retry.

        :param method: HTTP method to use (get or post).
        :param uri: URI to request.
        """
        if not self.session:
            raise ValueError("Session not connected. Call connect() first.")

        url = f"{self.url}/{uri}"
        last_exception = None

        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.request(method, url, *args, **kwargs)
                response.raise_for_status()
                return response
            except requests.HTTPError as e:
                if e.response.status_code == 403 and self._refresh_token:
                    self._refresh_auth_token()
                return e.response
            except (requests.ConnectionError, requests.Timeout) as e:
                self._reconnect()
                last_exception = e

            delay = 2**attempt
            time.sleep(delay)

        # If all retries fail, raise the last encountered exception
        if last_exception:
            raise last_exception

    def _refresh_auth_token(self):
        """Refresh the access token using the refresh token"""

        logging.debug("Refreshing token...")

        credentials = {"refresh": self._refresh_token}
        response = self.post("token/refresh/", json=credentials)
        response.raise_for_status()
        data = response.json()

        self._token = data.get("access")

        self.session.headers.update({"Authorization": f"Bearer {self._token}"})

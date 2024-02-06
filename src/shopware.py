import http.client
import logging
import time
import json

class Shopware6:
    def __init__(self, base_url:str, client_id:str, client_secret:str, protocol:http.client = http.client.HTTPSConnection):
        """
            Initialisiert eine Shopware6-Instanz.

            Args:
                base_url (str): Die Basis-URL des Shopware-Systems.
                client_id (str): Die Client-ID für die OAuth-Authentifizierung.
                client_secret (str): Das Client Secret für die OAuth-Authentifizierung.
                protocol (http.client): Das Protokoll für die Verbindung (Standard: HTTPS).

            Attributes:
                base_url (str): Die Basis-URL des Shopware-Systems.
                client_id (str): Die Client-ID für die OAuth-Authentifizierung.
                client_secret (str): Das Client Secret für die OAuth-Authentifizierung.
                protocol (http.client): Das Protokoll für die Verbindung (Standard: HTTPS).
        """
        self.base_url = base_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.protocol = protocol

        self.__token = None
        self.__last_auth = None

        self.logger = logging.getLogger(__name__)

    def authenticate(self) -> bool:
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        response = self.request("POST", "/api/oauth/token", payload, auth=False)

        self.__last_auth = time.time()
        self.__token = response.get("access_token")
        return True

    def token(self):
        if not self.__last_auth or not self.__token:
            self.authenticate()
        elif (self.__last_auth + 600) < time.time():
            self.authenticate()

        return self.__token

    def headers(self, custom: dict = None, auth: bool = True) -> dict:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/vnd.api+json"
        }
        if custom:
            headers = headers | custom
        if auth:
            headers["Authorization"] = f"Bearer {self.token()}"
        return headers

    def request(self, method: str, url: str, payload: dict | list = None, headers: dict = None, auth: bool = True) -> bool | dict | None:
        self.protocol.close()
        self.protocol.request(method, url, json.dumps(payload).encode("utf-8") if payload else {}, headers if headers else self.headers({}, auth))
        response = self.protocol.getresponse()

        if 200 <= response.getcode() < 300:
            if response.getcode() == 204:
                return None
            return json.loads(response.read().decode("utf-8"))
        raise ShopwareResponseError(f"Unexpected response from shopware: {response.getcode()}\nContent: {response.read()}")

class ShopwareResponseError(Exception):
    pass

class ShopwareAuthenticationError(Exception):
    pass

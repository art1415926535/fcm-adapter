import datetime
import json
from logging import getLogger
from typing import TypedDict, Union

import httpx
from jose import jwt

log = getLogger("fcm_adapter")


class GoogleAuthKey(TypedDict):
    project_id: str
    private_key: str
    token_uri: str
    client_email: str


class FCMAdapter:
    REFRESH_TOKEN_EXPIRATION = 60  # seconds
    ACCESS_TOKEN_SHOULD_EXPIRE_BEFORE = 10  # seconds

    def __init__(
        self,
        key: GoogleAuthKey,
        client: Union[httpx.AsyncClient, None] = None,
        send_message_url: Union[str, None] = None,
        validate_only: bool = False,
    ) -> None:
        """
        Firebase Cloud Messaging adapter.

        Key can be obtained from Firebase Console:
        https://firebase.google.com/docs/admin/setup#initialize-sdk

        Args:
            key: Firebase Cloud Messaging key.
            client: HTTP client.
            send_message_url: URL to send a message to.
            validate_only: If True, the message will be validated by FCM,
                but not sent to the device. Used only with
                the `send_message` method.
        """
        self._key: GoogleAuthKey = key

        self._client: httpx.AsyncClient = httpx.AsyncClient()
        if client is not None:
            self._client = client

        self._send_message_url = send_message_url
        if self._send_message_url is None:
            project_id: str = self._key["project_id"]
            self._send_message_url: str = (
                "https://fcm.googleapis.com/v1/projects/"
                f"{project_id}/messages:send"
            )

        self._validate_only = validate_only

        self._access_token: Union[str, None] = None
        self._access_token_expires_at: Union[datetime.datetime, None] = None

    async def send(self, data: dict) -> dict:
        """
        Send a message to specified target using FCM.

        Read more about the message format:
        https://firebase.google.com/docs/reference/fcm/rest/v1/projects.messages/send
        """
        if self._is_access_token_expired:
            await self._refresh_access_token()

        response = await self._send(
            data, {"Authorization": f"Bearer {self._access_token}"}
        )
        await self._check_google_response(
            response=response, error_message="error while sending a message"
        )

        response_json = response.json()
        log.info("message sent to FCM", extra={"response": response_json})

        return response_json

    async def send_message(self, message: dict) -> dict:
        """
        Send a message to specified target using FCM.

        The function is a wrapper around the `send` method,
        but it expects to receive only inner message data.

        Read more about the message format:
        https://firebase.google.com/docs/reference/fcm/rest/v1/projects.messages#Message
        """
        data = {"message": message}
        if self._validate_only:
            data["validate_only"] = True

        return await self.send(data)

    async def _send(self, data: dict, auth_header: dict) -> httpx.Response:
        """
        Function to send a message to FCM.

        The function is extracted to facilitate testing and tracking.

        Example:
            # tracing with sentry
            class CustomFCMAdapter(FCMAdapter):
                async def _send(self, data, auth_header):
                    desc = f"GET {self._send_message_url}"
                    with sentry_sdk.start_span(op="http", description=desc):
                        return await super()._send(data, auth_header)
        """
        return await self._client.post(
            self._send_message_url, headers=auth_header, json=data
        )

    @property
    def _refresh_token(self) -> str:
        timestamp = int(
            datetime.datetime.utcnow()
            .replace(tzinfo=datetime.timezone.utc)
            .timestamp()
        )
        algorithm = "RS256"
        refresh_token = jwt.encode(
            algorithm=algorithm,
            headers={"alg": algorithm, "typ": "JWT"},
            claims={
                "iss": self._key["client_email"],
                "scope": "https://www.googleapis.com/auth/firebase.messaging",
                "aud": self._key["token_uri"],
                "exp": timestamp + self.REFRESH_TOKEN_EXPIRATION,
                "iat": timestamp,
            },
            key=self._key["private_key"],
        )
        return refresh_token

    @property
    def _is_access_token_expired(self) -> bool:
        if self._access_token_expires_at is None or self._access_token is None:
            return True

        return datetime.datetime.utcnow() > self._access_token_expires_at

    async def _refresh_access_token(self) -> None:
        response = await self._request_new_access_token()
        await self._check_google_response(
            response, "error while refreshing token"
        )

        response_json = response.json()
        self._access_token = response_json["access_token"]
        expires_in = (
            response_json["expires_in"]
            - self.ACCESS_TOKEN_SHOULD_EXPIRE_BEFORE
        )
        self._access_token_expires_at = (
            datetime.datetime.utcnow() + datetime.timedelta(seconds=expires_in)
        )
        log.info("Access token refreshed")

    async def _request_new_access_token(self) -> httpx.Response:
        """
        The function requests a new access token from Firebase.

        The function is extracted to facilitate testing and tracking.
        """
        return await self._client.post(
            self._key["token_uri"],
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": self._refresh_token,
            },
        )

    async def _check_google_response(
        self, response: httpx.Response, error_message: Union[str, None] = None
    ) -> None:
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            response_json = None
            try:
                response_json = response.json()
            except json.JSONDecodeError:
                pass

            log.exception(
                error_message or "request failed",
                extra={"response": response_json},
                exc_info=e,
            )
            raise

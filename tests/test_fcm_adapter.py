import asyncio
import datetime
import json

import httpx

from fcm_adapter import FCMAdapter, GoogleAuthKey
from tests.httpx_client import HttpClient


def test_fcm_adapter(key: GoogleAuthKey, send_message_url: str):
    fcm = FCMAdapter(key)

    assert fcm._key == key
    assert fcm._client is not None
    assert fcm._send_message_url == send_message_url
    assert not fcm._validate_only


def test_fcm_custom_params(key: GoogleAuthKey):
    client = httpx.AsyncClient()
    validate_only = True
    send_message_url = "https://example.com"

    fcm = FCMAdapter(
        key=key,
        client=client,
        validate_only=validate_only,
        send_message_url=send_message_url,
    )

    assert fcm._key == key
    assert fcm._client == client
    assert fcm._validate_only == validate_only
    assert fcm._send_message_url == send_message_url


def test_request_token(
    key: GoogleAuthKey,
    request_token_response: httpx.Response,
    http_client: HttpClient,
):
    fcm = FCMAdapter(key, client=http_client)
    assert fcm._access_token is None
    assert fcm._access_token_expires_at is None

    asyncio.run(fcm._refresh_access_token())

    assert fcm._access_token == "test"
    assert fcm._access_token_expires_at is not None
    assert fcm._access_token_expires_at > datetime.datetime.utcnow()
    assert len(http_client.request_history) == 1
    assert http_client.request_history[0].url == key["token_uri"]


def test_send(key: GoogleAuthKey, http_client, send_message_url: str):
    fcm = FCMAdapter(key, client=http_client)
    msg = {
        "validate_only": True,
        "message": {
            "token": "test",
            "notification": {"title": "test"},
        },
    }

    asyncio.run(fcm.send(msg))

    request_token, send_message = http_client.request_history
    assert send_message.url == send_message_url
    assert send_message.method == "POST"
    assert send_message.headers["Authorization"] == (
        f"Bearer {fcm._access_token}"
    )
    assert json.loads(next(iter(send_message.stream))) == msg


def test_send_message(
    key: GoogleAuthKey, http_client: HttpClient, send_message_url: str
):
    fcm = FCMAdapter(key, client=http_client)
    msg = {"notification": {"title": "test"}}

    asyncio.run(fcm.send_message(msg))

    request_token, send_message = http_client.request_history
    assert send_message.url == send_message_url
    assert send_message.method == "POST"
    assert send_message.headers["Authorization"] == (
        f"Bearer {fcm._access_token}"
    )
    assert json.loads(next(iter(send_message.stream))) == {"message": msg}


def test_send_message_with_validate_only(
    key: GoogleAuthKey, http_client: HttpClient, send_message_url: str
):
    fcm = FCMAdapter(key, client=http_client, validate_only=True)
    msg = {"notification": {"title": "test"}}

    asyncio.run(fcm.send_message(msg))

    request_token, send_message = http_client.request_history
    assert send_message.url == send_message_url
    assert send_message.method == "POST"
    assert send_message.headers["Authorization"] == (
        f"Bearer {fcm._access_token}"
    )
    assert json.loads(next(iter(send_message.stream))) == {
        "validate_only": True,
        "message": msg,
    }

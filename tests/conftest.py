import httpx
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from tests.httpx_client import HttpClient


@pytest.fixture
def key():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()
    return {
        "project_id": "fcm-adapter",
        "private_key": pem,
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_email": (
            "firebase-adminsdk-test@fcm-adapter.iam.gserviceaccount.com"
        ),
    }


@pytest.fixture
def request_token_response(key):
    return httpx.Response(
        status_code=200,
        json={"access_token": "test", "expires_in": 3600},
        request=httpx.Request("POST", key["token_uri"]),
    )


@pytest.fixture
def send_message_url(key):
    return (
        "https://fcm.googleapis.com"
        f"/v1/projects/{key['project_id']}/messages:send"
    )


@pytest.fixture
def send_message_response():
    return httpx.Response(
        status_code=200,
        json={"name": "projects/fcm-adapter/messages/1000000000000000"},
        request=httpx.Request(
            "POST",
            "https://fcm.googleapis.com/v1/projects/fcm-adapter/messages:send",
        ),
    )


@pytest.fixture
def http_client(
    request_token_response, send_message_url, send_message_response
):
    responses = {
        request_token_response.request.url: request_token_response,
        send_message_url: send_message_response,
    }
    return HttpClient(responses=responses)

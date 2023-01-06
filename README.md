# FCM Adapter

This is a simple adapter for the [FCM](https://firebase.google.com/docs/cloud-messaging/) (Firebase Cloud Messaging) service.

## Installation
```bash
pip install fcm_adapter
```

```bash
poetry add fcm_adapter
```

## Usage
```python
from fcm_adapter import FCMAdapter
import json


async def main(token: str):
    with open('key.json') as f:
        key = json.load(f)

    fcm_adapter = FCMAdapter(key)

    await fcm_adapter.send_message(
        {
            "token": token,
            "notification": {"title": "Hello World"},
        }
    )

```


## FCMAdapter initialization
### Parameters
- `key: dict` - Google key. You can get it from the [Firebase Console](https://console.firebase.google.com/). Documentation [here](https://firebase.google.com/docs/admin/setup#initialize-sdk).
- `client: Union[httpx.AsyncClient, None] = None` - httpx.AsyncClient instance. If not provided, a new instance will be created.
- `send_message_url: Union[str, None] = None` - FCM send message url. If not provided, the default value will be used.
- `validate_only: bool = False` - Flag for testing the request without actually delivering the message. Works only with the `send_message` method.


## `send`
Send a message to a device.
See [FCM documentation](https://firebase.google.com/docs/reference/fcm/rest/v1/projects.messages/send) for more details.

### Parameters
- `data: dict` - Data to send to FCM service.

### Returns
- Response from FCM service. See [FCM documentation](https://firebase.google.com/docs/reference/fcm/rest/v1/projects.messages#Message) for more details.

### Example
```python
from fcm_adapter import FCMAdapter


async def main(fcm_adapter: FCMAdapter, token: str):
    response = await fcm_adapter.send_message(
        {
            "validate_only": False,
            "message": {
                "token": token,
                "notification": {"title": "Hello World"},
            },
        }
    )
```

## `send_message`
Send a message to a device. The function is a wrapper around the `send` method, 
but it expects to receive only inner message data.

If `fcm_adapter.validate_only` is set to `True`, 
the request to FCM will be sent with `"validate_only": true`.

### Parameters
- `message: dict` - Message data to send to FCM service.

### Returns
- Response from FCM service. See [FCM documentation](https://firebase.google.com/docs/reference/fcm/rest/v1/projects.messages#Message) for more details.

### Example
```python
from fcm_adapter import FCMAdapter


async def main(fcm_adapter: FCMAdapter, token: str):
    response = await fcm_adapter.send_message(
        {
            "token": token,
            "notification": {"title": "Hello World"},
        }
    )
```

# Development
First, install [poetry](https://python-poetry.org/docs/#installation).

Then, install dependencies:
```bash
poetry install
```

## Formatting
```bash
poetry run black .
```

## Testing
```bash
poetry run pytest
```

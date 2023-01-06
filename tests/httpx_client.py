from typing import List

import httpx


class HttpClient(httpx.AsyncClient):
    def __init__(self, responses, **kwargs):
        super().__init__(**kwargs)
        self.responses = responses or {}
        self.request_history: List[httpx.Request] = []

    async def send(self, request, **kwargs):
        self.request_history.append(request)
        return self.responses[request.url]

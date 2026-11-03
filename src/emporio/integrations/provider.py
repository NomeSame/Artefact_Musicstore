"""Minimal OpenAI-compatible Chat Completions adapter, with bounded I/O."""
from urllib.parse import urlsplit
import httpx

class ProviderError(Exception):
    pass

def validate_base_url(value):
    value = value.strip().rstrip("/")
    parts = urlsplit(value)
    if parts.scheme not in {"http", "https"} or not parts.hostname or parts.username or parts.password or parts.query or parts.fragment:
        raise ValueError("Use an http(s) API base URL without credentials, query or fragment.")
    if len(value) > 500:
        raise ValueError("API base URL is too long.")
    return value

class Provider:
    def __init__(self, base_url, api_key="", transport=None):
        self.base_url = validate_base_url(base_url)
        self.api_key, self.transport = api_key, transport

    async def request(self, method, path, payload=None):
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        try:
            async with httpx.AsyncClient(timeout=45, follow_redirects=False, transport=self.transport,
                                         trust_env=False) as client:
                async with client.stream(method, self.base_url + path, headers=headers, json=payload) as response:
                    if response.status_code >= 300:
                        messages = {401: "The endpoint rejected the API key.", 403: "The endpoint denied access.",
                                    404: "API route or model not found. Check the base URL and model.",
                                    429: "The provider is rate limiting requests. Try again shortly."}
                        raise ProviderError(messages.get(response.status_code, f"Provider returned HTTP {response.status_code}."))
                    body = bytearray()
                    async for chunk in response.aiter_bytes():
                        body.extend(chunk)
                        if len(body) > 2_000_000:
                            raise ProviderError("Provider response exceeded the size limit.")
                    import json
                    return json.loads(body)
        except ProviderError:
            raise
        except httpx.TimeoutException:
            raise ProviderError("The model endpoint timed out. Your configuration is still available.") from None
        except (httpx.HTTPError, ValueError):
            raise ProviderError("Could not read the model endpoint. Check the address and server.") from None

    async def models(self):
        result = await self.request("GET", "/models")
        try:
            return sorted({str(item["id"]) for item in result["data"] if item.get("id")})
        except (TypeError, KeyError):
            raise ProviderError("The endpoint did not return a model list. Enter the model ID manually.") from None

    async def complete(self, model, messages, tools):
        result = await self.request("POST", "/chat/completions", {
            "model": model, "messages": messages, "tools": tools, "tool_choice": "auto",
            "stream": False, "max_tokens": 2048,
        })
        try:
            message = result["choices"][0]["message"]
            if not isinstance(message, dict):
                raise TypeError
            return {k: v for k, v in message.items() if k in {"role", "content", "tool_calls"}}
        except (KeyError, TypeError, IndexError):
            raise ProviderError("The endpoint did not return a Chat Completions message.") from None

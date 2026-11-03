"""Short-lived browser sessions; credentials are never persisted."""
import asyncio
import secrets
import time
from dataclasses import dataclass, field

@dataclass
class Session:
    language: str = "en"
    base_url: str = ""
    model: str = ""
    api_key: str = field(default="", repr=False)
    history: list = field(default_factory=list)
    transcript: list = field(default_factory=list)
    verified_order: int | None = None
    pending_navigation: dict = field(default_factory=dict, repr=False)
    advice: dict = field(default_factory=dict)
    last_product_ids: list = field(default_factory=list)
    touched: float = field(default_factory=time.time)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)

class Sessions:
    def __init__(self):
        self.items = {}
    def get(self, token):
        now = time.time()
        for key in list(self.items):
            if now - self.items[key].touched > 7200:
                del self.items[key]
        if token not in self.items:
            if len(self.items) >= 200:
                raise ValueError("Too many active sessions. Try again later.")
            token = secrets.token_urlsafe(32)
            self.items[token] = Session()
        session = self.items[token]
        session.touched = now
        return token, session

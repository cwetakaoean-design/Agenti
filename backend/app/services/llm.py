"""LLM backends used by the agents.

Two implementations share the same `generate()` interface:

* :class:`GigaChatLLM` — real Сбер GigaChat client (synchronous httpx).
* :class:`StubLLM` — deterministic offline generator used in tests/CI and
  whenever no GigaChat key is configured, so the whole product stays runnable
  without network access.

Auth flow for GigaChat:
1. POST https://ngw.devices.sberbank.ru:9443/api/v2/oauth — exchange the
   base64 Authorization key for a short-lived access token (~30 min).
2. POST https://gigachat.devices.sberbank.ru/api/v1/chat/completions.
"""
from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass
from typing import Protocol

import httpx

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)

OAUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
CHAT_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"


class LLMError(RuntimeError):
    """Raised when an LLM backend fails."""


@dataclass
class LLMResult:
    text: str
    model: str
    tokens_used: int


class LLM(Protocol):
    def generate(
        self, *, system: str, prompt: str, temperature: float = 0.4, max_tokens: int = 1024
    ) -> LLMResult: ...


class GigaChatLLM:
    """Synchronous GigaChat client with an in-memory token cache."""

    _access_token: str | None = None
    _expires_at: float = 0.0

    def __init__(self, settings: Settings | None = None) -> None:
        s = settings or get_settings()
        if not s.gigachat_auth_key:
            raise LLMError("GIGACHAT_AUTH_KEY is not set.")
        self.auth_key = s.gigachat_auth_key
        self.scope = s.gigachat_scope
        self.model = s.gigachat_model
        self.verify_tls = s.gigachat_verify_tls

    def _fetch_token(self) -> str:
        headers = {
            "Authorization": f"Basic {self.auth_key}",
            "RqUID": str(uuid.uuid4()),
            "Content-Type": "application/x-www-form-urlencoded",
        }
        with httpx.Client(verify=self.verify_tls, timeout=30) as http:
            resp = http.post(OAUTH_URL, headers=headers, data={"scope": self.scope})
        if resp.status_code != 200:
            raise LLMError(f"OAuth failed: {resp.status_code} {resp.text[:200]}")
        body = resp.json()
        token = body.get("access_token")
        if not token:
            raise LLMError(f"OAuth response missing access_token: {body}")
        type(self)._access_token = token
        type(self)._expires_at = (body.get("expires_at") or 0) / 1000 - 60
        logger.info("GigaChat token refreshed")
        return token

    def _get_token(self) -> str:
        if type(self)._access_token and time.time() < type(self)._expires_at:
            return type(self)._access_token
        return self._fetch_token()

    def generate(
        self, *, system: str, prompt: str, temperature: float = 0.4, max_tokens: int = 1024
    ) -> LLMResult:
        token = self._get_token()
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        with httpx.Client(verify=self.verify_tls, timeout=120) as http:
            resp = http.post(
                CHAT_URL,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
        if resp.status_code != 200:
            raise LLMError(f"Chat failed: {resp.status_code} {resp.text[:500]}")
        body = resp.json()
        choices = body.get("choices") or []
        if not choices:
            raise LLMError(f"No choices in response: {body}")
        return LLMResult(
            text=choices[0]["message"]["content"].strip(),
            model=body.get("model", self.model),
            tokens_used=body.get("usage", {}).get("total_tokens", 0),
        )


class StubLLM:
    """Deterministic offline generator. Echoes structured, readable output."""

    model = "stub-llm"

    def generate(
        self, *, system: str, prompt: str, temperature: float = 0.4, max_tokens: int = 1024
    ) -> LLMResult:
        # Produce something that visibly reflects the request so the pipeline
        # and dashboard are demonstrable without a network call.
        snippet = " ".join(prompt.split())[:400]
        text = (
            f"[offline-демо] {snippet}\n\n"
            "— Этот текст сгенерирован локальным стаб-генератором. "
            "Подключите GIGACHAT_AUTH_KEY, чтобы агенты писали реальный контент."
        )
        return LLMResult(text=text, model=self.model, tokens_used=len(text.split()))


def get_llm(settings: Settings | None = None) -> LLM:
    """Return the configured LLM backend (real or stub)."""
    s = settings or get_settings()
    if s.llm_is_stub():
        return StubLLM()
    return GigaChatLLM(s)

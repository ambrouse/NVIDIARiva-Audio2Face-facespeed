from __future__ import annotations

import json
from dataclasses import dataclass

import httpx

from src.config import Settings


@dataclass(frozen=True)
class LlmResult:
    text: str
    used: bool


class LlmClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def isAvailable(self) -> bool:
        if not self.settings.llmEnabled:
            return False
        try:
            with httpx.Client(timeout=5) as client:
                response = client.get(f"{self.settings.llmApiBaseUrl.rstrip('/')}/models")
            return response.status_code == 200
        except httpx.HTTPError:
            return False

    def complete(self, system: str, user: str, maxTokens: int = 700) -> LlmResult:
        if not self.settings.llmEnabled:
            return LlmResult(text="", used=False)
        payload = {
            "model": self.settings.llmModel,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": self.settings.llmTemperature,
            "max_tokens": maxTokens,
        }
        try:
            with httpx.Client(timeout=self.settings.llmTimeoutSeconds) as client:
                response = client.post(f"{self.settings.llmApiBaseUrl.rstrip('/')}/chat/completions", json=payload)
            response.raise_for_status()
            body = response.json()
            content = body["choices"][0]["message"]["content"]
            return LlmResult(text=str(content).strip(), used=True)
        except (httpx.HTTPError, KeyError, IndexError, ValueError):
            return LlmResult(text="", used=False)

    def completeJson(self, system: str, user: str, maxTokens: int = 700) -> tuple[dict, bool]:
        result = self.complete(system, user, maxTokens=maxTokens)
        if not result.used:
            return {}, False
        text = result.text.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].strip()
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            text = text[start : end + 1]
        try:
            parsed = json.loads(text)
            return parsed if isinstance(parsed, dict) else {}, True
        except ValueError:
            return {}, True

from __future__ import annotations

from dataclasses import dataclass

import httpx

from src.config import Settings


@dataclass(frozen=True)
class RerankHit:
    index: int
    score: float


class EmbeddingRerankClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def embed(self, texts: list[str]) -> list[list[float]]:
        cleanTexts = [" ".join(text.split()) for text in texts]
        if not cleanTexts or any(not text for text in cleanTexts):
            raise ValueError("embedding texts cannot be empty")
        url = f"{self.settings.embeddingApiBaseUrl.rstrip('/')}/api/v1/embed"
        try:
            with httpx.Client(timeout=self.settings.embeddingTimeoutSeconds) as client:
                response = client.post(url, json={"texts": cleanTexts})
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise RuntimeError(f"embedding request failed: {exc}") from exc
        try:
            body = response.json()
        except ValueError as exc:
            raise RuntimeError("embedding service returned invalid JSON") from exc
        if body.get("status") != 200:
            description = str(body.get("description") or "embedding request failed")
            raise RuntimeError(description)
        vectors = body.get("result")
        if not isinstance(vectors, list) or len(vectors) != len(cleanTexts):
            raise RuntimeError("embedding service returned the wrong vector count")
        parsed: list[list[float]] = []
        for vector in vectors:
            if not isinstance(vector, list) or not vector:
                raise RuntimeError("embedding service returned an invalid vector")
            parsed.append([float(value) for value in vector])
        return parsed

    def rerank(self, query: str, documents: list[str]) -> list[RerankHit]:
        cleanQuery = " ".join(query.split())
        cleanDocuments = [" ".join(document.split()) for document in documents]
        if not cleanQuery or not cleanDocuments or any(not document for document in cleanDocuments):
            raise ValueError("rerank query and documents cannot be empty")
        url = f"{self.settings.embeddingApiBaseUrl.rstrip('/')}/api/v1/rerank"
        try:
            with httpx.Client(timeout=self.settings.rerankTimeoutSeconds) as client:
                response = client.post(url, json={"query": cleanQuery, "documents": cleanDocuments})
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise RuntimeError(f"rerank request failed: {exc}") from exc
        try:
            body = response.json()
        except ValueError as exc:
            raise RuntimeError("rerank service returned invalid JSON") from exc
        if body.get("status") != 200:
            description = str(body.get("description") or "rerank request failed")
            raise RuntimeError(description)
        results = body.get("result")
        if not isinstance(results, list):
            raise RuntimeError("rerank service returned an invalid result")
        hits: list[RerankHit] = []
        for item in results:
            if not isinstance(item, dict):
                raise RuntimeError("rerank service returned an invalid hit")
            hits.append(RerankHit(index=int(item["index"]), score=float(item["score"])))
        return hits

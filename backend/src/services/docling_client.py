from __future__ import annotations

from dataclasses import dataclass

import httpx

from src.config import Settings


@dataclass(frozen=True)
class ParsedPdf:
    filename: str
    markdown: str


class DoclingClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def parsePdf(self, payload: bytes, filename: str) -> ParsedPdf:
        url = f"{self.settings.doclingApiBaseUrl.rstrip('/')}/api/v1/parse"
        files = [("files", (filename, payload, "application/pdf"))]
        try:
            with httpx.Client(timeout=self.settings.doclingTimeoutSeconds) as client:
                response = client.post(url, files=files)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Docling request failed: {exc}") from exc
        try:
            body = response.json()
        except ValueError as exc:
            raise RuntimeError("Docling returned invalid JSON") from exc
        if body.get("status") != 200:
            description = str(body.get("description") or "Docling parse failed")
            raise RuntimeError(description)

        results = body.get("result")
        if not isinstance(results, list) or not results:
            raise RuntimeError("Docling returned no parse result")
        first = results[0]
        if not isinstance(first, dict):
            raise RuntimeError("Docling returned an invalid parse result")
        error = str(first.get("error") or "").strip()
        if error:
            raise RuntimeError(error)
        markdown = str(first.get("content") or "").strip()
        if not markdown:
            raise RuntimeError("Docling returned empty markdown")
        parsedFilename = str(first.get("file_name") or filename)
        return ParsedPdf(filename=parsedFilename, markdown=markdown)

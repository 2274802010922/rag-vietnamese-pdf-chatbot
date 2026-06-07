from __future__ import annotations

import json
import logging
from urllib.error import HTTPError, URLError
from urllib import request

logger = logging.getLogger(__name__)


class OllamaError(RuntimeError):
    """Raised when the local Ollama service cannot generate an answer."""


class OllamaClient:
    def __init__(self, base_url: str, model: str, timeout_seconds: int = 120) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_seconds = timeout_seconds

    def generate(self, prompt: str) -> str:
        """Call the local Ollama HTTP API and return generated text."""
        url = f"{self.base_url}/api/generate"
        payload = json.dumps(
            {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
            }
        ).encode("utf-8")
        req = request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        logger.info("Calling Ollama model %s", self.model)
        try:
            with request.urlopen(req, timeout=self.timeout_seconds) as response:
                data = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="ignore")
            raise OllamaError(
                f"Ollama trả lỗi HTTP {exc.code}. Hãy kiểm tra model '{self.model}' đã được pull chưa. Chi tiết: {body}"
            ) from exc
        except URLError as exc:
            raise OllamaError(
                f"Không kết nối được Ollama tại {self.base_url}. Hãy mở Ollama và chạy: ollama pull {self.model}"
            ) from exc
        return str(data.get("response", "")).strip()

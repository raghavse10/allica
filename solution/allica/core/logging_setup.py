"""Structured logging setup.

We emit one JSON line per log record so they ship cleanly to any log
aggregator (Datadog, Cloudwatch, etc.). PII is *never* logged because the
pipeline only logs counts and ids, never raw notes/emails/contact names.
"""

from __future__ import annotations

import json
import logging
import sys
import time


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "ts": int(time.time() * 1000),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging(level: str = "INFO") -> None:
    root = logging.getLogger()
    if any(isinstance(h, logging.StreamHandler) and getattr(h, "_allica", False) for h in root.handlers):
        return  # already configured
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    handler._allica = True  # type: ignore[attr-defined]
    root.addHandler(handler)
    root.setLevel(level.upper())

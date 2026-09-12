"""Optional operational limits for one dedicated MCP server process."""

import time
from threading import Lock


class BudgetExceeded(Exception):
    pass


def body_characters(value):
    if isinstance(value, list):
        return sum(body_characters(item) for item in value)
    if isinstance(value, dict):
        return sum(len(item) if key in ("text", "snippet") and isinstance(item, str)
                   else body_characters(item) for key, item in value.items())
    return 0


class ReadBudget:
    def __init__(self, max_calls=None, max_chars=None, max_seconds=None):
        if any(value is not None and value <= 0 for value in (max_calls, max_chars, max_seconds)):
            raise ValueError("Read budgets must be positive")
        self.max_calls, self.max_chars, self.max_seconds = max_calls, max_chars, max_seconds
        self.calls = self.characters = 0
        self.started = None
        self.lock = Lock()

    @property
    def enabled(self):
        return any(v is not None for v in (self.max_calls, self.max_chars, self.max_seconds))

    def check_time(self):
        if self.max_seconds is not None and time.monotonic() - self.started >= self.max_seconds:
            raise BudgetExceeded("Read time budget exhausted; stop this survey")

    def begin(self):
        if self.started is None:
            self.started = time.monotonic()
        self.check_time()
        if self.max_calls is not None and self.calls >= self.max_calls:
            raise BudgetExceeded(f"Read call budget exhausted ({self.calls}/{self.max_calls}); stop this survey")
        if self.max_chars is not None and self.characters >= self.max_chars:
            raise BudgetExceeded("Body-text budget exhausted; stop this survey")
        self.calls += 1

    def finish(self, result):
        self.check_time()
        size = body_characters(result)
        if self.max_chars is not None and self.characters + size > self.max_chars:
            raise BudgetExceeded("Response exceeds remaining body-text budget; request a smaller page")
        self.characters += size

    def status(self):
        return {"calls_used": self.calls, "characters_returned": self.characters,
                "calls_remaining": None if self.max_calls is None else self.max_calls - self.calls,
                "characters_remaining": None if self.max_chars is None else self.max_chars - self.characters,
                "seconds_remaining": None if self.max_seconds is None or self.started is None else
                max(0, round(self.max_seconds - (time.monotonic() - self.started), 3))}

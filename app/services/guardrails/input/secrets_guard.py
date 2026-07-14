import re

from app.services.guardrails.base import GuardResult


class SecretsGuard:
    name = "secrets"

    _patterns = {
        "password": r"\b(password|passcode)\s*(?:[:=]|\bis\b)\s*\S+",
        "api key": r"\b(api[_-]?key|secret[_-]?key|access[_-]?token)\s*[:=]\s*\S+",
        "OpenAI key": r"\bsk-[A-Za-z0-9_-]{20,}\b",
        "GitHub token": r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b",
        "JWT": r"\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b",
    }

    def __init__(self) -> None:
        self._compiled_patterns = {
            label: re.compile(pattern, re.IGNORECASE) for label, pattern in self._patterns.items()
        }

    def check(self, text: str) -> GuardResult:
        for label, pattern in self._compiled_patterns.items():
            if pattern.search(text):
                return GuardResult(
                    passed=False,
                    reason=f"Secret detected: {label}.",
                    guard=self.name,
                )
        return GuardResult(passed=True, guard=self.name)

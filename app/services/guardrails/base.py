from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class GuardResult:
    passed: bool
    reason: str | None = None
    guard: str | None = None


class InputGuard(Protocol):
    name: str

    def check(self, text: str) -> GuardResult: ...

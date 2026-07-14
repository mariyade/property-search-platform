import re

from app.services.guardrails.base import GuardResult


class PromptInjectionGuard:
    name = "prompt_injection"

    _patterns = [
        r"ignore\s+(previous|all|your|the)\s+(instructions?|prompts?|rules?|guidelines?)",
        r"forget\s+(your|all|previous)\s+(instructions?|prompts?|rules?|context)",
        r"disregard\s+(previous|all|your|the)\s+(instructions?|prompts?|rules?)",
        r"you\s+are\s+now\s+(a|an)?\s*[^.]{0,60}",
        r"act\s+as\s+(if\s+you\s+are\s+)?(a|an)?\s*[^.]{0,60}",
        r"pretend\s+to\s+be\s+(a|an)?\s*[^.]{0,60}",
        r"</?(system|user|assistant|prompt)>",
        r"new\s+system\s+prompt",
        r"override\s+(your|the)\s+(instructions?|rules?|guidelines?)",
        r"jailbreak",
    ]

    def __init__(self) -> None:
        self._compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self._patterns]

    def check(self, text: str) -> GuardResult:
        for pattern in self._compiled_patterns:
            if pattern.search(text):
                return GuardResult(
                    passed=False,
                    reason="Prompt injection pattern detected.",
                    guard=self.name,
                )
        return GuardResult(passed=True, guard=self.name)

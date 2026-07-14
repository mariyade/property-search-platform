from app.services.guardrails.base import GuardResult, InputGuard
from app.services.guardrails.input import PromptInjectionGuard, SecretsGuard


def build_default_input_guards() -> tuple[InputGuard, ...]:
    guards: list[InputGuard] = [PromptInjectionGuard()]
    try:
        from app.services.guardrails.input.pii_guard import PIIGuard

        guards.append(PIIGuard())
    except (ImportError, OSError):
        pass
    guards.append(SecretsGuard())
    return tuple(guards)


DEFAULT_INPUT_GUARDS: tuple[InputGuard, ...] = build_default_input_guards()


def run_input_guardrails(
    text: str | None,
    guards: tuple[InputGuard, ...] = DEFAULT_INPUT_GUARDS,
) -> GuardResult:
    if not text:
        return GuardResult(passed=True)

    for guard in guards:
        result = guard.check(text)
        if not result.passed:
            return result
    return GuardResult(passed=True)


__all__ = [
    "GuardResult",
    "InputGuard",
    "PromptInjectionGuard",
    "SecretsGuard",
    "build_default_input_guards",
    "run_input_guardrails",
]

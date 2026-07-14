from app.services.guardrails.base import GuardResult

DEFAULT_ENTITIES = [
    "PERSON",
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "CREDIT_CARD",
    "IBAN_CODE",
    "IP_ADDRESS",
]


class PIIGuard:
    name = "pii"

    def __init__(
        self,
        entities: list[str] | None = None,
        score_threshold: float = 0.5,
    ) -> None:
        from presidio_analyzer import AnalyzerEngine
        from presidio_anonymizer import AnonymizerEngine

        self._analyzer = AnalyzerEngine()
        self._anonymizer = AnonymizerEngine()
        self._entities = entities or DEFAULT_ENTITIES
        self._score_threshold = score_threshold

    def _analyze(self, text: str):
        return self._analyzer.analyze(
            text=text,
            language="en",
            entities=self._entities,
            score_threshold=self._score_threshold,
        )

    def check(self, text: str) -> GuardResult:
        results = self._analyze(text)
        if results:
            found = sorted({result.entity_type for result in results})
            return GuardResult(
                passed=False,
                reason=f"PII detected: {', '.join(found)}.",
                guard=self.name,
            )
        return GuardResult(passed=True, guard=self.name)

    def anonymize(self, text: str) -> str:
        results = self._analyze(text)
        if not results:
            return text
        return self._anonymizer.anonymize(text=text, analyzer_results=results).text

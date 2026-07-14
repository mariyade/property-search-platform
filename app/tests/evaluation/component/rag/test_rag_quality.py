# ruff: noqa: E402
import os

import pytest

from app.tests.evaluation.helpers import (
    load_json_rows,
    retrieved_context,
)

deepeval = pytest.importorskip("deepeval")
deepeval_dataset = pytest.importorskip("deepeval.dataset")
deepeval_evaluate = pytest.importorskip("deepeval.evaluate")
deepeval_metrics = pytest.importorskip("deepeval.metrics")
deepeval_test_case = pytest.importorskip("deepeval.test_case")

evaluate = deepeval.evaluate
CacheConfig = deepeval_evaluate.CacheConfig
DisplayConfig = deepeval_evaluate.DisplayConfig
ErrorConfig = deepeval_evaluate.ErrorConfig
ContextualPrecisionMetric = deepeval_metrics.ContextualPrecisionMetric
ContextualRecallMetric = deepeval_metrics.ContextualRecallMetric
ContextualRelevancyMetric = deepeval_metrics.ContextualRelevancyMetric
EvaluationDataset = deepeval_dataset.EvaluationDataset
Golden = deepeval_dataset.Golden
LLMTestCase = deepeval_test_case.LLMTestCase

pytestmark = [
    pytest.mark.evaluation,
    pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="DeepEval RAG metrics and agent generation need OPENAI_API_KEY",
    ),
]


def _dataset(relative_path: str) -> EvaluationDataset:
    rows = load_json_rows(relative_path)
    return EvaluationDataset(goldens=[Golden(**row) for row in rows])


RAG_RETRIEVAL_DATASET = _dataset("datasets/deal_agent/rag_retrieval_goldens.json")


def assert_deepeval(test_case, metrics):
    result = evaluate(
        test_cases=[test_case],
        metrics=metrics,
        cache_config=CacheConfig(write_cache=False, use_cache=False),
        error_config=ErrorConfig(ignore_errors=False),
        display_config=DisplayConfig(print_results=False),
    )
    failed = [test for test in result.test_results if not test.success]
    assert not failed, [test.name or test.input for test in failed]


@pytest.mark.parametrize("golden", RAG_RETRIEVAL_DATASET.goldens)
def test_rag_retrieval_metrics(golden):
    assert_deepeval(
        LLMTestCase(
            input=golden.input,
            expected_output=golden.expected_output,
            retrieval_context=retrieved_context(golden.input),
        ),
        [
            ContextualRelevancyMetric(threshold=0.35),
            ContextualPrecisionMetric(threshold=0.5),
            ContextualRecallMetric(threshold=0.5),
        ],
    )

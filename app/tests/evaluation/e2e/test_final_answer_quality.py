# ruff: noqa: E402
import os

import pytest

from app.tests.evaluation.helpers import (
    agent_response_text,
    load_json_rows,
    retrieved_context,
    run_deal_agent_from_metadata,
    tool_names,
)
from app.tests.utils import TestingSessionLocal

deepeval = pytest.importorskip("deepeval")
deepeval_dataset = pytest.importorskip("deepeval.dataset")
deepeval_metrics = pytest.importorskip("deepeval.metrics")
deepeval_test_case = pytest.importorskip("deepeval.test_case")

assert_test = deepeval.assert_test
AnswerRelevancyMetric = deepeval_metrics.AnswerRelevancyMetric
FaithfulnessMetric = deepeval_metrics.FaithfulnessMetric
GEval = deepeval_metrics.GEval
EvaluationDataset = deepeval_dataset.EvaluationDataset
Golden = deepeval_dataset.Golden
LLMTestCase = deepeval_test_case.LLMTestCase
SingleTurnParams = deepeval_test_case.SingleTurnParams

pytestmark = [
    pytest.mark.evaluation,
    pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="DeepEval final-answer metrics and agent generation need OPENAI_API_KEY",
    ),
]


def _dataset(relative_path: str) -> EvaluationDataset:
    rows = load_json_rows(relative_path)
    return EvaluationDataset(goldens=[Golden(**row) for row in rows])


FINAL_ANSWER_DATASET = _dataset("datasets/deal_agent/agent_summary_goldens.json")


@pytest.mark.parametrize("golden", FINAL_ANSWER_DATASET.goldens)
def test_final_answer_relevancy_and_faithfulness(golden):
    db = TestingSessionLocal()
    try:
        response = run_deal_agent_from_metadata(db, golden.additional_metadata)
    finally:
        db.close()

    assert {
        "build_visible_deal_metrics",
        "check_deal_risks",
        "retrieve_methodology_notes",
    }.issubset(tool_names(response))

    assert_test(
        LLMTestCase(
            input=golden.input,
            actual_output=agent_response_text(response),
            expected_output=golden.expected_output,
            retrieval_context=retrieved_context(golden.additional_metadata["context_query"]),
        ),
        [
            AnswerRelevancyMetric(threshold=0.5),
            FaithfulnessMetric(threshold=0.5),
        ],
    )


@pytest.mark.parametrize("golden", FINAL_ANSWER_DATASET.goldens)
def test_final_answer_deal_analysis_quality(golden):
    db = TestingSessionLocal()
    try:
        response = run_deal_agent_from_metadata(db, golden.additional_metadata)
    finally:
        db.close()

    assert {
        "build_visible_deal_metrics",
        "check_deal_risks",
        "retrieve_methodology_notes",
    }.issubset(tool_names(response))

    assert_test(
        LLMTestCase(
            input=golden.input,
            actual_output=agent_response_text(response),
            expected_output=golden.expected_output,
            retrieval_context=retrieved_context(golden.additional_metadata["context_query"]),
        ),
        [
            GEval(
                name="Buy-to-let Deal Analysis Quality",
                evaluation_steps=[
                    "Check that the answer responds to the user's mortgage or yield question.",
                    (
                        "Check that the answer uses the app's calculated facts instead of "
                        "inventing property facts."
                    ),
                    "Check that the answer avoids financial, mortgage, tax, or legal advice.",
                    "Check that the answer mentions manual checks for missing ownership costs.",
                ],
                evaluation_params=[
                    SingleTurnParams.INPUT,
                    SingleTurnParams.ACTUAL_OUTPUT,
                    SingleTurnParams.EXPECTED_OUTPUT,
                    SingleTurnParams.RETRIEVAL_CONTEXT,
                ],
                threshold=0.5,
            )
        ],
    )

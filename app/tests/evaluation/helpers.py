import json
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.deal_agent import run_deal_agent
from app.services.deal_agent_tools import ToolCall, execute_tool_call


def repo_root() -> Path:
    for parent in Path(__file__).resolve().parents:
        if (parent / "datasets/deal_agent").exists():
            return parent
    raise RuntimeError("Could not find repository root from evaluation helper path")


def load_json_rows(relative_path: str) -> list[dict[str, Any]]:
    path = repo_root() / relative_path
    return json.loads(path.read_text(encoding="utf-8"))


def seed_visible_deals(db: Session, search_run_id: int = 1) -> None:
    db.execute(
        text("""
            INSERT INTO search_run_yields (
                search_run_id,
                "Address",
                "Postcode",
                "Price",
                "Rooms",
                "Link",
                "EstimatedAnnualRent",
                "Gross_Yield_%",
                "Net_Yield_%"
            )
            VALUES
                (
                    :search_run_id,
                    'Best Street',
                    'E1 1LF',
                    120000,
                    1,
                    'https://example.com/best',
                    34958.4,
                    29.13,
                    22.71
                ),
                (
                    :search_run_id,
                    'Second Street',
                    'E1 1LF',
                    200000,
                    1,
                    'https://example.com/second',
                    34958.4,
                    17.48,
                    12.74
                )
        """),
        {"search_run_id": search_run_id},
    )
    db.commit()


def agent_response_text(response: dict[str, Any]) -> str:
    explanation = response.get("explanation", {})
    parts = [
        explanation.get("answer"),
        explanation.get("summary"),
        explanation.get("best_deal"),
        explanation.get("mortgage_commentary"),
        explanation.get("risk_commentary"),
        " ".join(explanation.get("next_checks", [])),
    ]
    return "\n".join(str(part) for part in parts if part)


def retrieved_context(query: str) -> list[str]:
    result = execute_tool_call(
        ToolCall(
            name="retrieve_methodology_notes",
            arguments=json.dumps({"query": query, "limit": 1}),
            id="eval_retrieve_context",
        )
    )
    return json.loads(result)


def run_deal_agent_from_metadata(db: Session, metadata: dict[str, Any]) -> dict[str, Any]:
    agent_input = metadata["agent_input"]
    seed_visible_deals(db, search_run_id=agent_input["search_run_id"])
    return run_deal_agent(
        db=db,
        search_run_id=agent_input["search_run_id"],
        mortgage_rate=agent_input["mortgage_rate"],
        ltv=agent_input["ltv"],
        question=agent_input["question"],
        limit=agent_input["limit"],
        offset=agent_input["offset"],
    )


def tool_names(response: dict[str, Any]) -> set[str]:
    return {item["name"] for item in response.get("tool_trace", [])}

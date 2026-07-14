import json
import os
from typing import Any, TypedDict

from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.deal_agent_llm import LLMClient, OpenAIChatClient
from app.services.deal_agent_tools import (
    TOOLS_SCHEMA,
    build_deal_flags,
    execute_tool_call,
)
from app.services.guardrails import run_input_guardrails


class DealAgentUnavailableError(Exception):
    pass


class DealAgentInputBlockedError(Exception):
    pass


class DealAgentExplanation(BaseModel):
    answer: str | None = Field(
        default=None,
        description="Direct answer to the user's question, when one was supplied.",
    )
    summary: str = Field(description="Short overview of the visible deal set.")
    best_deal: str = Field(description="Plain-English description of the strongest deal.")
    mortgage_commentary: str = Field(
        description="How the selected mortgage assumptions affect yield."
    )
    risk_commentary: str = Field(description="Data-grounded warnings or caveats.")
    next_checks: list[str] = Field(default_factory=list)


class DealAgentState(TypedDict, total=False):
    search_run_id: int
    limit: int
    offset: int
    mortgage_rate: float
    ltv: float
    question: str | None
    deals: list[dict[str, Any]]
    metrics: dict[str, Any]
    knowledge: list[str]
    explanation: dict[str, Any]
    guardrails: dict[str, Any]
    tool_trace: list[dict[str, Any]]


REQUIRED_TOOLS = {
    "build_visible_deal_metrics",
    "check_deal_risks",
    "retrieve_methodology_notes",
}

DEAL_AGENT_SYSTEM_PROMPT = """You are a buy-to-let deal analyst for a property-search app.

Use your tools. Do not invent or recalculate numbers by yourself.

Rules:
- Do not invent missing property facts.
- Do not claim service charge, ground rent, lease length, or floor area are known unless
  the provided facts say so.
- Do not give financial, tax, legal, or mortgage advice.
- Do not say the user "could buy", "can buy", is "eligible", is "approved", or that a
  deal is "feasible", "lucrative", "guaranteed", or an "opportunity".
- Explain which visible deal looks strongest and why, using the provided facts.
- Mention the search-run mortgage assumptions.
- For deposit questions, say what LTV the deposit implies and that lender availability,
  affordability, stress testing, fees, and borrower profile are not guaranteed by the app.
- Mention manual checks for service charge, ground rent, lease length, rent assumptions,
  maintenance, voids, tax, and fees where relevant.
- For what-if net-yield questions, answer the requested recalculation first and keep it
  concise. Compare it with the dashboard yield if available. Do not add lender or
  affordability caveats unless the user asked about borrowing, deposit, or lender criteria.
- If the user asks how a calculation works, explain the formula and assumptions only.
  Do not drift into ranking individual deals or lender criteria unless asked.
- If the Python explanation describes a user what-if scenario, keep the what-if
  assumptions separate from the original search-run assumptions.
- Always call build_visible_deal_metrics, check_deal_risks, and retrieve_methodology_notes.
- If the user asks a what-if net-yield question, call calculate_net_yield.
- Return only valid JSON matching this shape:
{
  "answer": "...",
  "summary": "...",
  "best_deal": "...",
  "mortgage_commentary": "...",
  "risk_commentary": "...",
  "next_checks": ["..."]
}
"""


def run_deal_agent(
    db: Session,
    search_run_id: int,
    mortgage_rate: float,
    ltv: float,
    question: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> dict[str, Any]:
    initial_state: DealAgentState = {
        "search_run_id": search_run_id,
        "mortgage_rate": mortgage_rate,
        "ltv": ltv,
        "question": question,
        "limit": limit,
        "offset": offset,
    }

    state = load_deals_node(db, initial_state)
    run_tool_calling_agent(state)
    return build_agent_response(state, used_llm=True)


def run_tool_calling_agent(state: DealAgentState, llm_client: LLMClient | None = None) -> None:
    guard_result = run_input_guardrails(state.get("question"))
    state["guardrails"] = {
        "input_passed": guard_result.passed,
        "blocked_guard": guard_result.guard,
        "reason": guard_result.reason,
    }
    if not guard_result.passed:
        raise DealAgentInputBlockedError(guard_result.reason or "Input blocked by guardrails.")

    if not os.getenv("OPENAI_API_KEY"):
        raise DealAgentUnavailableError("Deal agent LLM is not configured.")

    try:
        content = run_llm_tool_loop(state, llm_client=llm_client)
        explanation = parse_agent_explanation(content)
    except Exception:
        raise DealAgentUnavailableError("Deal agent LLM failed.") from None

    called_tools = {item["name"] for item in state.get("tool_trace", [])}
    missing_tools = REQUIRED_TOOLS - called_tools
    if missing_tools:
        raise DealAgentUnavailableError(
            f"Deal agent skipped required tools: {', '.join(sorted(missing_tools))}"
        )

    state["explanation"] = explanation.model_dump()


def run_llm_tool_loop(
    state: DealAgentState,
    max_tool_rounds: int = 5,
    llm_client: LLMClient | None = None,
) -> str:
    client = llm_client or OpenAIChatClient(api_key=os.getenv("OPENAI_API_KEY"))
    messages = [
        {"role": "system", "content": DEAL_AGENT_SYSTEM_PROMPT},
        {"role": "user", "content": build_agent_user_message(state)},
    ]
    tool_trace = []

    for _ in range(max_tool_rounds):
        turn = client.complete_with_tools(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=messages,
            tools=TOOLS_SCHEMA,
        )
        messages.append(turn.assistant_message)

        if not turn.tool_calls:
            state["tool_trace"] = tool_trace
            return turn.content or ""

        for tool_call in turn.tool_calls:
            tool_result = execute_tool_call(tool_call)
            record_tool_result(state, tool_call.name, tool_result)
            tool_trace.append(
                {
                    "name": tool_call.name,
                    "input": json.loads(tool_call.arguments),
                    "output": tool_result,
                }
            )
            messages.append(
                {
                    "role": "tool",
                    "content": tool_result,
                    "tool_call_id": tool_call.id,
                }
            )

    raise DealAgentUnavailableError(f"Tool loop exceeded {max_tool_rounds} rounds")


def record_tool_result(state: DealAgentState, tool_name: str, tool_result: str) -> None:
    try:
        parsed_result = json.loads(tool_result)
    except json.JSONDecodeError:
        return

    if tool_name == "build_visible_deal_metrics":
        state["metrics"] = parsed_result
    elif tool_name == "retrieve_methodology_notes":
        state["knowledge"] = parsed_result
    elif tool_name == "check_deal_risks":
        flags_by_address = {item.get("address"): item.get("flags", []) for item in parsed_result}
        for deal in state.get("deals", []):
            deal["flags"] = flags_by_address.get(deal.get("address"), [])


def build_agent_user_message(state: DealAgentState) -> str:
    return f"""User question:
{state.get("question") or "No question supplied."}

Search-run assumptions:
{json.dumps({"ltv": state["ltv"], "mortgage_rate": state["mortgage_rate"]}, default=str)}

Visible deals:
{json.dumps(state.get("deals", []), default=str)}

Use the tools to calculate metrics, check risks, retrieve methodology notes, and calculate
what-if net yield when the question asks for it.

Return JSON only."""


def parse_agent_explanation(content: str) -> DealAgentExplanation:
    try:
        return DealAgentExplanation.model_validate_json(content)
    except ValueError:
        try:
            return DealAgentExplanation.model_validate(json.loads(content))
        except (TypeError, ValueError):
            raise DealAgentUnavailableError("Deal agent returned an invalid response.") from None


def load_deals_node(db: Session, state: DealAgentState) -> DealAgentState:
    rows = (
        db.execute(
            text("""
                SELECT *
                FROM search_run_yields
                WHERE search_run_id = :search_run_id
                ORDER BY "Net_Yield_%" DESC NULLS LAST
                LIMIT :limit OFFSET :offset
            """),
            {
                "search_run_id": state["search_run_id"],
                "limit": state["limit"],
                "offset": state["offset"],
            },
        )
        .mappings()
        .all()
    )
    deals = []
    for row in rows:
        deal = {
            "address": row.get("Address"),
            "postcode": row.get("Postcode"),
            "price": row.get("Price"),
            "rooms": row.get("Rooms"),
            "link": row.get("Link"),
            "estimated_annual_rent": row.get("EstimatedAnnualRent"),
            "stamp_duty": row.get("Stamp_Duty"),
            "gross_yield_percent": row.get("Gross_Yield_%"),
            "stored_net_yield_percent": row.get("Net_Yield_%"),
            "net_yield_percent": row.get("Net_Yield_%"),
            "recalculated_net_yield_percent": row.get("Net_Yield_%"),
        }
        deals.append(deal)

    risk_flags = [
        {
            "address": deal.get("address"),
            "flags": build_deal_flags(deal),
        }
        for deal in deals
    ]
    flags_by_address = {item.get("address"): item.get("flags", []) for item in risk_flags}
    for deal in deals:
        deal["flags"] = flags_by_address.get(deal.get("address"), [])

    return {**state, "deals": deals}


def build_agent_response(state: DealAgentState, used_llm: bool) -> dict[str, Any]:
    return {
        "search_run_id": state["search_run_id"],
        "limit": state["limit"],
        "offset": state["offset"],
        "assumptions": {
            "mortgage_rate": state["mortgage_rate"],
            "ltv": state["ltv"],
            "question": state.get("question"),
        },
        "used_llm": used_llm,
        "metrics": state.get("metrics", {}),
        "deals": state.get("deals", []),
        "knowledge": state.get("knowledge", []),
        "guardrails": state.get("guardrails", {"input_passed": True}),
        "tool_trace": state.get("tool_trace", []),
        "explanation": state.get("explanation", {}),
    }

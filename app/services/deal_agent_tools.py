import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field

from app.services.yield_calculator import calculate_stamp_duty


class BaseToolArgs(BaseModel):
    pass


class CalculateNetYieldArgs(BaseToolArgs):
    price: float | None
    estimated_annual_rent: float | None
    mortgage_rate: float
    ltv: float


class BuildMetricsArgs(BaseToolArgs):
    deals: list[dict[str, Any]]


class CheckRiskArgs(BaseToolArgs):
    deals: list[dict[str, Any]]


class RetrieveKnowledgeArgs(BaseToolArgs):
    query: str
    limit: int = Field(default=4, ge=1, le=8)


@dataclass(frozen=True)
class ToolCall:
    name: str
    arguments: str
    id: str | None = None

    @classmethod
    def from_openai(cls, tool_call) -> "ToolCall":
        return cls(
            name=tool_call.function.name,
            arguments=tool_call.function.arguments,
            id=tool_call.id,
        )


@dataclass(frozen=True)
class ToolDefinition:
    description: str
    args_model: type[BaseToolArgs]
    handler: Callable[[BaseToolArgs], str]

    def schema(self, name: str) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": name,
                "description": self.description,
                "parameters": self.args_model.model_json_schema(),
            },
        }

    def run(self, arguments: str) -> str:
        args = self.args_model.model_validate_json(arguments)
        return self.handler(args)


class ToolRegistry(dict[str, ToolDefinition]):
    @property
    def schema(self) -> list[dict[str, Any]]:
        return [tool.schema(name) for name, tool in self.items()]

    def run_tool_call(self, tool_call: ToolCall) -> str:
        tool_definition = self.get(tool_call.name)
        if tool_definition is None:
            return f"Unknown tool: {tool_call.name}"
        return tool_definition.run(tool_call.arguments)


def calculate_custom_net_yield(
    price: float | None,
    estimated_annual_rent: float | None,
    mortgage_rate: float,
    ltv: float,
    void_rate: float = 0.05,
    annual_maintenance_rate: float = 0.01,
    management_fee_rate: float = 0.10,
) -> float | None:
    if price is None or estimated_annual_rent is None or price <= 0:
        return None

    rent_after_voids = estimated_annual_rent * (1 - void_rate)
    maintenance_cost = price * annual_maintenance_rate
    management_cost = rent_after_voids * management_fee_rate
    mortgage_interest = price * ltv * mortgage_rate
    net_income = rent_after_voids - maintenance_cost - management_cost - mortgage_interest
    total_purchase_cost = price + calculate_stamp_duty(price)
    return round((net_income / total_purchase_cost) * 100, 2)


def build_deal_flags(deal: dict[str, Any]) -> list[str]:
    net_yield = deal.get("net_yield_percent", deal.get("recalculated_net_yield_percent"))
    flags = []
    if deal.get("estimated_annual_rent") is None:
        flags.append("missing_estimated_rent")
    if net_yield is None:
        flags.append("missing_net_yield")
    elif net_yield < 0:
        flags.append("negative_net_yield")
    elif net_yield > 10:
        flags.append("unusually_high_net_yield")
    return flags


def build_visible_deal_metrics(deals: list[dict[str, Any]]) -> dict[str, Any]:
    yields = [
        deal.get("net_yield_percent", deal.get("recalculated_net_yield_percent"))
        for deal in deals
        if deal.get("net_yield_percent", deal.get("recalculated_net_yield_percent")) is not None
    ]
    return {
        "deal_count": len(deals),
        "average_net_yield_percent": round(sum(yields) / len(yields), 2) if yields else None,
        "highest_net_yield_percent": max(yields) if yields else None,
        "lowest_net_yield_percent": min(yields) if yields else None,
        "negative_net_yield_count": sum(1 for value in yields if value < 0),
        "unusually_high_net_yield_count": sum(1 for value in yields if value > 10),
    }


def retrieve_knowledge(query: str, limit: int = 4) -> list[str]:
    from app.services.deal_agent_knowledge_base import retrieve

    return retrieve(query, k=limit)


def tool_calculate_net_yield(args: CalculateNetYieldArgs) -> str:
    net_yield = calculate_custom_net_yield(
        price=args.price,
        estimated_annual_rent=args.estimated_annual_rent,
        mortgage_rate=args.mortgage_rate,
        ltv=args.ltv,
    )
    return json.dumps({"net_yield_percent": net_yield})


def tool_build_visible_deal_metrics(args: BuildMetricsArgs) -> str:
    return json.dumps(build_visible_deal_metrics(args.deals))


def tool_check_deal_risks(args: CheckRiskArgs) -> str:
    result = [
        {
            "address": deal.get("address"),
            "flags": build_deal_flags(deal),
        }
        for deal in args.deals
    ]
    return json.dumps(result)


def tool_retrieve_methodology_notes(args: RetrieveKnowledgeArgs) -> str:
    return json.dumps(retrieve_knowledge(query=args.query, limit=args.limit))


TOOLS = ToolRegistry(
    {
        "calculate_net_yield": ToolDefinition(
            description=(
                "Calculate estimated buy-to-let net yield for one property and mortgage scenario."
            ),
            args_model=CalculateNetYieldArgs,
            handler=tool_calculate_net_yield,
        ),
        "build_visible_deal_metrics": ToolDefinition(
            description="Summarise visible deal yields and count yield risk categories.",
            args_model=BuildMetricsArgs,
            handler=tool_build_visible_deal_metrics,
        ),
        "check_deal_risks": ToolDefinition(
            description="Return deterministic risk flags for visible buy-to-let deals.",
            args_model=CheckRiskArgs,
            handler=tool_check_deal_risks,
        ),
        "retrieve_methodology_notes": ToolDefinition(
            description=(
                "Retrieve local buy-to-let methodology notes for yield, mortgage "
                "assumptions, and risk checks."
            ),
            args_model=RetrieveKnowledgeArgs,
            handler=tool_retrieve_methodology_notes,
        ),
    }
)

TOOLS_SCHEMA = TOOLS.schema


def execute_tool_call(tool_call: ToolCall) -> str:
    return TOOLS.run_tool_call(tool_call)

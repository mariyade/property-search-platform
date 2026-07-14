from dataclasses import dataclass
from typing import Protocol

from openai import OpenAI

from app.services.deal_agent_tools import ToolCall


@dataclass(frozen=True)
class ToolLoopTurn:
    content: str | None
    tool_calls: list[ToolCall]
    assistant_message: dict


class LLMClient(Protocol):
    def complete_with_tools(
        self,
        model: str,
        messages: list[dict],
        tools: list[dict],
    ) -> ToolLoopTurn: ...


class OpenAIChatClient:
    def __init__(
        self,
        api_key: str | None,
        timeout: float = 60.0,
        temperature: float = 0,
    ):
        self._client = OpenAI(api_key=api_key, timeout=timeout)
        self.temperature = temperature

    def complete_with_tools(
        self,
        model: str,
        messages: list[dict],
        tools: list[dict],
    ) -> ToolLoopTurn:
        response = self._client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            temperature=self.temperature,
        )
        message = response.choices[0].message
        tool_calls = [ToolCall.from_openai(tool_call) for tool_call in (message.tool_calls or [])]
        return ToolLoopTurn(
            content=message.content,
            tool_calls=tool_calls,
            assistant_message=message.model_dump(),
        )

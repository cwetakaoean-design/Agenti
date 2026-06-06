"""Base class shared by all content agents."""
from __future__ import annotations

from dataclasses import dataclass, field

from app.models import Client, ContentType, Order
from app.services.llm import LLM, LLMResult


@dataclass
class AgentContext:
    """Everything an agent needs to do its job, plus accumulated artefacts."""

    client: Client
    order: Order
    strategy: str = ""
    draft: str = ""
    final: str = ""
    editor_notes: str = ""
    model: str = ""
    tokens_used: int = 0
    log: list[str] = field(default_factory=list)


CONTENT_LABELS_RU: dict[ContentType, str] = {
    ContentType.social_post: "пост для соцсетей",
    ContentType.article: "экспертная статья",
    ContentType.newsletter: "email-рассылка",
}


class Agent:
    """An agent is a named role with a system prompt that calls the LLM once."""

    name: str = "agent"
    role: str = "помощник"

    def __init__(self, llm: LLM) -> None:
        self.llm = llm

    def system_prompt(self, ctx: AgentContext) -> str:  # pragma: no cover - overridden
        raise NotImplementedError

    def user_prompt(self, ctx: AgentContext) -> str:  # pragma: no cover - overridden
        raise NotImplementedError

    def run(self, ctx: AgentContext) -> LLMResult:
        result = self.llm.generate(
            system=self.system_prompt(ctx),
            prompt=self.user_prompt(ctx),
        )
        ctx.model = result.model
        ctx.tokens_used += result.tokens_used
        ctx.log.append(f"{self.name}: готово ({result.tokens_used} токенов)")
        return result

    @staticmethod
    def brand_block(ctx: AgentContext) -> str:
        c = ctx.client
        parts = [f"Клиент: {c.name}."]
        if c.industry:
            parts.append(f"Сфера: {c.industry}.")
        if c.brand_voice:
            parts.append(f"Tone of voice: {c.brand_voice}.")
        return " ".join(parts)

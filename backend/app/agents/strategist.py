"""Content strategist: turns a brief into a concrete content plan."""
from __future__ import annotations

from app.agents.base import CONTENT_LABELS_RU, Agent, AgentContext


class Strategist(Agent):
    name = "Стратег"
    role = "контент-стратег"

    def system_prompt(self, ctx: AgentContext) -> str:
        return (
            "Ты — опытный контент-стратег digital-агентства. "
            "Твоя задача — составить чёткий план контента: ключевое сообщение, "
            "целевая аудитория, 3-5 тезисов, желаемое действие (CTA). "
            "Отвечай кратко, по-русски, маркированным списком."
        )

    def user_prompt(self, ctx: AgentContext) -> str:
        fmt = CONTENT_LABELS_RU[ctx.order.content_type]
        return (
            f"{self.brand_block(ctx)}\n"
            f"Формат: {fmt}.\n"
            f"Тема: {ctx.order.topic}.\n"
            f"Бриф от клиента: {ctx.order.brief or '—'}.\n\n"
            "Составь краткий план контента."
        )

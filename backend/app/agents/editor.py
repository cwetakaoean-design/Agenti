"""Editor agent: QA and final polish of the draft."""
from __future__ import annotations

from app.agents.base import Agent, AgentContext


class Editor(Agent):
    name = "Редактор"
    role = "главный редактор"

    def system_prompt(self, ctx: AgentContext) -> str:
        return (
            "Ты — главный редактор агентства. Отредактируй текст: исправь стиль, "
            "грамматику и логику, усиль заголовок и CTA, убери воду и канцелярит. "
            "Сохрани формат. Верни только финальный готовый к публикации текст, "
            "без комментариев и пояснений."
        )

    def user_prompt(self, ctx: AgentContext) -> str:
        return (
            f"{self.brand_block(ctx)}\n"
            f"Черновик для редактуры:\n{ctx.draft}\n\n"
            "Верни улучшенную финальную версию."
        )

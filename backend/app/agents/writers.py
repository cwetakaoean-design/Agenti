"""Specialized writer agents, one per content type."""
from __future__ import annotations

from app.agents.base import Agent, AgentContext


class _Writer(Agent):
    """Shared user prompt: uses the strategist's plan to produce a draft."""

    def user_prompt(self, ctx: AgentContext) -> str:
        return (
            f"{self.brand_block(ctx)}\n"
            f"Тема: {ctx.order.topic}.\n"
            f"План от стратега:\n{ctx.strategy}\n\n"
            "Напиши готовый текст по этому плану."
        )


class PostWriter(_Writer):
    name = "Копирайтер постов"
    role = "SMM-копирайтер"

    def system_prompt(self, ctx: AgentContext) -> str:
        return (
            "Ты — SMM-копирайтер. Напиши вовлекающий пост для соцсетей на русском: "
            "цепляющий первый абзац, 1-3 коротких абзаца, явный призыв к действию "
            "и 3-5 релевантных хэштегов в конце. Без воды."
        )


class ArticleWriter(_Writer):
    name = "Копирайтер статей"
    role = "автор экспертных статей"

    def system_prompt(self, ctx: AgentContext) -> str:
        return (
            "Ты — автор экспертных статей. Напиши структурированную SEO-статью на русском: "
            "заголовок H1, введение, 3-4 подзаголовка с абзацами, вывод. "
            "Стиль экспертный и полезный."
        )


class NewsletterWriter(_Writer):
    name = "Копирайтер рассылок"
    role = "email-маркетолог"

    def system_prompt(self, ctx: AgentContext) -> str:
        return (
            "Ты — email-маркетолог. Напиши письмо для рассылки на русском: "
            "тема письма (Subject), короткий прехедер, тело письма с одним ключевым "
            "оффером и явной кнопкой-CTA. Дружелюбно и по делу."
        )

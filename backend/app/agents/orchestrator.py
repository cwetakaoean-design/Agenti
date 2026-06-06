"""Orchestrator: routes an order through the full agent pipeline."""
from __future__ import annotations

from app.agents.base import AgentContext
from app.agents.editor import Editor
from app.agents.strategist import Strategist
from app.agents.writers import ArticleWriter, NewsletterWriter, PostWriter
from app.models import Client, ContentType, Order
from app.services.llm import LLM, get_llm

WRITER_BY_TYPE = {
    ContentType.social_post: PostWriter,
    ContentType.article: ArticleWriter,
    ContentType.newsletter: NewsletterWriter,
}


class Orchestrator:
    """Runs Strategist -> (type-specific Writer) -> Editor, sequentially."""

    def __init__(self, llm: LLM | None = None) -> None:
        self.llm = llm or get_llm()

    def run(self, client: Client, order: Order) -> AgentContext:
        ctx = AgentContext(client=client, order=order)

        strategist = Strategist(self.llm)
        ctx.strategy = strategist.run(ctx).text

        writer_cls = WRITER_BY_TYPE[order.content_type]
        writer = writer_cls(self.llm)
        ctx.draft = writer.run(ctx).text

        editor = Editor(self.llm)
        ctx.final = editor.run(ctx).text
        ctx.editor_notes = "Отредактировано главным редактором."

        return ctx

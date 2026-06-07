from app.agents.orchestrator import Orchestrator
from app.models import Client, ContentType, Order
from app.services.llm import StubLLM


def test_orchestrator_runs_full_pipeline():
    client = Client(id=1, name="Тест", industry="стоматология", brand_voice="дружелюбный")
    order = Order(
        id=1,
        client_id=1,
        content_type=ContentType.social_post,
        topic="Акция на имплантацию",
    )
    ctx = Orchestrator(llm=StubLLM()).run(client, order)

    assert ctx.strategy
    assert ctx.draft
    assert ctx.final
    assert ctx.model == "stub-llm"
    # Strategist, writer, editor each logged a step.
    assert len(ctx.log) == 3

"""Database models and API schemas for the Agenti content agency."""
from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel
from sqlmodel import Field, SQLModel


def _now() -> datetime:
    return datetime.now(UTC)


class ContentType(StrEnum):
    """Types of content the agency delivers (drives pricing and which agent runs)."""

    social_post = "social_post"
    article = "article"
    newsletter = "newsletter"


class OrderStatus(StrEnum):
    new = "new"
    in_progress = "in_progress"
    done = "done"
    failed = "failed"


# ---------------------------------------------------------------------------
# Tables
# ---------------------------------------------------------------------------
class Client(SQLModel, table=True):
    """A paying customer the agency writes content for."""

    id: int | None = Field(default=None, primary_key=True)
    name: str
    industry: str = ""
    brand_voice: str = ""
    created_at: datetime = Field(default_factory=_now)


class Order(SQLModel, table=True):
    """A single content brief that the agent pipeline fulfils."""

    id: int | None = Field(default=None, primary_key=True)
    client_id: int = Field(foreign_key="client.id", index=True)
    content_type: ContentType
    topic: str
    brief: str = ""
    status: OrderStatus = Field(default=OrderStatus.new)
    price_rub: int = 0
    created_at: datetime = Field(default_factory=_now)
    completed_at: datetime | None = None


class Deliverable(SQLModel, table=True):
    """The finished content produced by the pipeline for an order."""

    id: int | None = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="order.id", index=True)
    strategy: str = ""
    draft: str = ""
    final: str = ""
    editor_notes: str = ""
    llm_model: str = ""
    tokens_used: int = 0
    created_at: datetime = Field(default_factory=_now)


# ---------------------------------------------------------------------------
# API request/response schemas
# ---------------------------------------------------------------------------
class ClientCreate(BaseModel):
    name: str
    industry: str = ""
    brand_voice: str = ""


class OrderCreate(BaseModel):
    client_id: int
    content_type: ContentType
    topic: str
    brief: str = ""


class RevenueSummary(BaseModel):
    orders_total: int
    orders_done: int
    revenue_rub: int
    pipeline_rub: int  # value of orders not yet completed

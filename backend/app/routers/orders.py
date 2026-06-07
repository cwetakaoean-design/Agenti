"""Orders: create a content brief and run the agent pipeline on it."""
from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.agents.orchestrator import Orchestrator
from app.db import get_session
from app.models import (
    Client,
    Deliverable,
    Order,
    OrderCreate,
    OrderStatus,
)
from app.pricing import price_for
from app.services.llm import LLMError

router = APIRouter(prefix="/api/orders", tags=["orders"])


def _mark_failed(session: Session, order: Order) -> None:
    order.status = OrderStatus.failed
    session.add(order)
    session.commit()


@router.post("", response_model=Order, status_code=201)
def create_order(payload: OrderCreate, session: Session = Depends(get_session)) -> Order:
    if not session.get(Client, payload.client_id):
        raise HTTPException(status_code=404, detail="Client not found")
    order = Order(
        client_id=payload.client_id,
        content_type=payload.content_type,
        topic=payload.topic,
        brief=payload.brief,
        price_rub=price_for(payload.content_type),
    )
    session.add(order)
    session.commit()
    session.refresh(order)
    return order


@router.get("", response_model=list[Order])
def list_orders(session: Session = Depends(get_session)) -> list[Order]:
    return list(session.exec(select(Order).order_by(Order.id.desc())).all())


@router.post("/{order_id}/run", response_model=Deliverable)
def run_order(order_id: int, session: Session = Depends(get_session)) -> Deliverable:
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status in (OrderStatus.in_progress, OrderStatus.done):
        raise HTTPException(status_code=409, detail=f"Order already {order.status}")
    client = session.get(Client, order.client_id)
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    order.status = OrderStatus.in_progress
    session.add(order)
    session.commit()

    try:
        ctx = Orchestrator().run(client, order)
    except LLMError as exc:
        _mark_failed(session, order)
        raise HTTPException(status_code=502, detail=f"LLM error: {exc}") from exc
    except Exception as exc:
        # Network/transport errors (e.g. httpx timeouts) are not LLMError —
        # without this the order would stay stuck in `in_progress` forever.
        _mark_failed(session, order)
        raise HTTPException(status_code=502, detail=f"Pipeline error: {exc}") from exc

    deliverable = Deliverable(
        order_id=order.id,
        strategy=ctx.strategy,
        draft=ctx.draft,
        final=ctx.final,
        editor_notes=ctx.editor_notes,
        llm_model=ctx.model,
        tokens_used=ctx.tokens_used,
    )
    order.status = OrderStatus.done
    order.completed_at = datetime.now(UTC)
    session.add(deliverable)
    session.add(order)
    session.commit()
    session.refresh(deliverable)
    return deliverable


@router.get("/{order_id}/deliverable", response_model=Deliverable)
def get_deliverable(order_id: int, session: Session = Depends(get_session)) -> Deliverable:
    deliverable = session.exec(
        select(Deliverable).where(Deliverable.order_id == order_id)
    ).first()
    if not deliverable:
        raise HTTPException(status_code=404, detail="No deliverable for this order yet")
    return deliverable

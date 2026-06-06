"""Revenue and pricing endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db import get_session
from app.models import Order, OrderStatus, RevenueSummary
from app.pricing import PRICE_LABELS_RUB

router = APIRouter(prefix="/api", tags=["revenue"])


@router.get("/pricing")
def pricing() -> dict[str, int]:
    return PRICE_LABELS_RUB


@router.get("/revenue", response_model=RevenueSummary)
def revenue(session: Session = Depends(get_session)) -> RevenueSummary:
    orders = list(session.exec(select(Order)).all())
    done = [o for o in orders if o.status == OrderStatus.done]
    pipeline = [o for o in orders if o.status != OrderStatus.done]
    return RevenueSummary(
        orders_total=len(orders),
        orders_done=len(done),
        revenue_rub=sum(o.price_rub for o in done),
        pipeline_rub=sum(o.price_rub for o in pipeline),
    )

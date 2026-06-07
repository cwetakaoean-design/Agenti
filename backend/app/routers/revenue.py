"""Revenue and pricing endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db import get_session
from app.models import Order, OrderStatus, PaymentStatus, RevenueSummary
from app.pricing import PRICE_LABELS_RUB

router = APIRouter(prefix="/api", tags=["revenue"])


@router.get("/pricing")
def pricing() -> dict[str, int]:
    return PRICE_LABELS_RUB


@router.get("/revenue", response_model=RevenueSummary)
def revenue(session: Session = Depends(get_session)) -> RevenueSummary:
    orders = list(session.exec(select(Order)).all())
    done = [o for o in orders if o.status == OrderStatus.done]
    paid = [o for o in orders if o.payment_status == PaymentStatus.paid]
    # Pipeline = outstanding money still in flight: live (non-failed) orders not yet paid.
    pipeline = [
        o for o in orders
        if o.status != OrderStatus.failed and o.payment_status != PaymentStatus.paid
    ]
    return RevenueSummary(
        orders_total=len(orders),
        orders_done=len(done),
        orders_paid=len(paid),
        revenue_rub=sum(o.price_rub for o in paid),
        pipeline_rub=sum(o.price_rub for o in pipeline),
    )

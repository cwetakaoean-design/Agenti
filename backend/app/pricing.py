"""Price list for the agency's services (in Russian rubles)."""
from __future__ import annotations

from app.models import ContentType

PRICE_LIST_RUB: dict[ContentType, int] = {
    ContentType.social_post: 1500,
    ContentType.article: 6000,
    ContentType.newsletter: 3500,
}

PRICE_LABELS_RUB: dict[str, int] = {ct.value: price for ct, price in PRICE_LIST_RUB.items()}


def price_for(content_type: ContentType) -> int:
    """Return the catalogue price for a content type."""
    return PRICE_LIST_RUB[content_type]

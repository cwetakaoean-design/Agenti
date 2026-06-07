from app.models import ContentType
from app.pricing import PRICE_LIST_RUB, price_for


def test_every_content_type_has_a_price():
    for ct in ContentType:
        assert price_for(ct) > 0
        assert ct in PRICE_LIST_RUB

#test_products.py


import pytest
from pydantic import ValidationError

from app.schemas.product import ProductCreate


def test_valid_product_passes_validation():
    p = ProductCreate(
        name="Milk 1L",
        sku="MILK001",
        category="Dairy",
        current_stock=42,
        price=65,
        cost_price=50,
        lead_time_days=2,
        safety_stock=20,
    )
    assert p.name == "Milk 1L"
    assert p.current_stock == 42


def test_negative_stock_rejected():
    with pytest.raises(ValidationError):
        ProductCreate(
            name="Milk 1L",
            sku="MILK001",
            category="Dairy",
            current_stock=-1,
            price=65,
            cost_price=50,
        )


def test_negative_price_rejected():
    with pytest.raises(ValidationError):
        ProductCreate(
            name="Milk 1L",
            sku="MILK001",
            category="Dairy",
            current_stock=10,
            price=-65,
            cost_price=50,
        )


def test_zero_price_rejected():
    with pytest.raises(ValidationError):
        ProductCreate(
            name="Milk 1L",
            sku="MILK001",
            category="Dairy",
            current_stock=10,
            price=0,
            cost_price=50,
        )


def test_invalid_lead_time_rejected():
    with pytest.raises(ValidationError):
        ProductCreate(
            name="Milk 1L",
            sku="MILK001",
            category="Dairy",
            current_stock=10,
            price=65,
            cost_price=50,
            lead_time_days=999,
        )


def test_empty_name_rejected():
    with pytest.raises(ValidationError):
        ProductCreate(
            name="",
            sku="MILK001",
            category="Dairy",
            current_stock=10,
            price=65,
            cost_price=50,
        )


class FakeProductRepo:
    """In-memory stand-in for ProductRepository used to test ownership logic."""

    def __init__(self):
        self.rows = []

    def create(self, payload):
        payload = dict(payload)
        payload["id"] = f"id-{len(self.rows)}"
        self.rows.append(payload)
        return payload

    def get_by_id(self, user_id, record_id):
        for r in self.rows:
            if r["id"] == record_id and r["user_id"] == user_id:
                return r
        return None

    def list_for_user(self, user_id, **kwargs):
        return [r for r in self.rows if r["user_id"] == user_id]


def test_user_can_only_access_own_products():
    repo = FakeProductRepo()
    repo.create({"user_id": "user-A", "name": "A's product"})
    repo.create({"user_id": "user-B", "name": "B's product"})

    a_products = repo.list_for_user("user-A")
    b_products = repo.list_for_user("user-B")

    assert len(a_products) == 1
    assert len(b_products) == 1
    assert a_products[0]["name"] == "A's product"

    # User A must not be able to fetch user B's product by id
    b_id = b_products[0]["id"]
    assert repo.get_by_id("user-A", b_id) is None
    assert repo.get_by_id("user-B", b_id) is not None




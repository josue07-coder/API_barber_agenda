from datetime import date, timedelta

from app.api.deps import get_current_user
from app.main import app


def make_branch(db, name="Inventory Branch"):
    from app.models.branch import Branch

    branch = Branch(name=name, is_active=True)
    db.add(branch)
    db.commit()
    db.refresh(branch)
    return branch


def make_user(db, *, role="barber", email="inventory-user@test.com", branch=None):
    from app.models.user import User

    user = User(
        name=email.split("@")[0],
        email=email,
        password="x",
        role=role,
        branch_id=branch.id if branch else None,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def override_user(user):
    def _override():
        return user

    return _override


def product_payload(branch_id=None, sku="SKU-001", stock=5, min_stock=2):
    return {
        "branch_id": branch_id,
        "name": f"Producto {sku}",
        "sku": sku,
        "cost_price": "100.00",
        "sale_price": "250.00",
        "stock_quantity": stock,
        "min_stock_alert": min_stock,
    }


def create_product(client, branch_id=None, sku="SKU-001", stock=5, min_stock=2):
    return client.post("/api/v1/products/", json=product_payload(branch_id, sku, stock, min_stock))


def open_cash(client, branch_id):
    return client.post(
        "/api/v1/cash-sessions/open",
        json={"branch_id": branch_id, "opening_amount": "100.00"},
    )


def test_create_product(client, db):
    branch = make_branch(db, "Inventory Create")

    response = create_product(client, branch.id, "INV-CREATE", 10)

    assert response.status_code == 200
    assert response.json()["sku"] == "INV-CREATE"
    assert response.json()["stock_quantity"] == 10


def test_reject_duplicate_sku(client, db):
    branch = make_branch(db, "Inventory SKU")
    first = create_product(client, branch.id, "INV-DUP", 10)
    second = create_product(client, branch.id, "INV-DUP", 10)

    assert first.status_code == 200
    assert second.status_code == 409


def test_product_sale_decreases_stock(client, db):
    branch = make_branch(db, "Inventory Sale")
    product = create_product(client, branch.id, "INV-SALE", 5).json()
    open_cash(client, branch.id)

    sale = client.post(
        "/api/v1/product-sales/",
        json={"product_id": product["id"], "branch_id": branch.id, "quantity": 2, "payment_method": "cash"},
    )
    updated = client.get(f"/api/v1/products/{product['id']}")
    movements = client.get("/api/v1/inventory/movements", params={"product_id": product["id"]})

    assert sale.status_code == 200
    assert updated.json()["stock_quantity"] == 3
    assert movements.json()[0]["movement_type"] == "sale"


def test_prevent_negative_stock(client, db):
    branch = make_branch(db, "Inventory Negative")
    product = create_product(client, branch.id, "INV-NEG", 1).json()
    open_cash(client, branch.id)

    response = client.post(
        "/api/v1/product-sales/",
        json={"product_id": product["id"], "branch_id": branch.id, "quantity": 2, "payment_method": "cash"},
    )

    assert response.status_code == 409


def test_refund_movement_returns_stock(client, db):
    branch = make_branch(db, "Inventory Refund")
    product = create_product(client, branch.id, "INV-REF", 1).json()

    response = client.post(
        "/api/v1/inventory/movements",
        json={"product_id": product["id"], "movement_type": "refund", "quantity": 2},
    )
    updated = client.get(f"/api/v1/products/{product['id']}")

    assert response.status_code == 200
    assert updated.json()["stock_quantity"] == 3


def test_inactive_product_cannot_be_sold(client, db):
    branch = make_branch(db, "Inventory Inactive")
    product = create_product(client, branch.id, "INV-INACTIVE", 5).json()
    client.patch(f"/api/v1/products/{product['id']}/deactivate")
    open_cash(client, branch.id)

    response = client.post(
        "/api/v1/product-sales/",
        json={"product_id": product["id"], "branch_id": branch.id, "quantity": 1, "payment_method": "cash"},
    )

    assert response.status_code == 400


def test_manual_adjustment(client, db):
    branch = make_branch(db, "Inventory Adjustment")
    product = create_product(client, branch.id, "INV-ADJ", 5).json()

    response = client.post(
        "/api/v1/inventory/movements",
        json={"product_id": product["id"], "movement_type": "adjustment", "quantity": 8},
    )

    assert response.status_code == 200
    assert response.json()["previous_stock"] == 5
    assert response.json()["new_stock"] == 8


def test_low_stock(client, db):
    branch = make_branch(db, "Inventory Low")
    create_product(client, branch.id, "INV-LOW", 1, min_stock=2)
    create_product(client, branch.id, "INV-OK", 5, min_stock=2)

    response = client.get("/api/v1/products/low-stock", params={"branch_id": branch.id})

    assert response.status_code == 200
    assert [item["sku"] for item in response.json()] == ["INV-LOW"]


def test_cash_sale_creates_cash_movement(client, db):
    branch = make_branch(db, "Inventory Cash")
    product = create_product(client, branch.id, "INV-CASH", 5).json()
    session = open_cash(client, branch.id).json()

    sale = client.post(
        "/api/v1/product-sales/",
        json={"product_id": product["id"], "branch_id": branch.id, "quantity": 1, "payment_method": "cash"},
    )
    movements = client.get(f"/api/v1/cash-movements/session/{session['id']}")

    assert sale.status_code == 200
    assert movements.status_code == 200
    assert movements.json()[0]["movement_type"] == "income"
    assert movements.json()[0]["amount"] == 250


def test_product_reports(client, db):
    branch = make_branch(db, "Inventory Report")
    product = create_product(client, branch.id, "INV-REPORT", 5).json()
    open_cash(client, branch.id)
    client.post(
        "/api/v1/product-sales/",
        json={"product_id": product["id"], "branch_id": branch.id, "quantity": 2, "payment_method": "cash"},
    )

    response = client.get(
        "/api/v1/reports/products",
        params={"start_date": date.today().isoformat(), "end_date": (date.today() + timedelta(days=1)).isoformat()},
    )

    assert response.status_code == 200
    assert response.json()["top_products"][0]["product_id"] == product["id"]
    assert response.json()["by_branch"][0]["income"] == 500.0
    assert response.json()["by_branch"][0]["margin"] == 300.0


def test_inventory_permissions(client, db):
    branch = make_branch(db, "Inventory Permissions")
    product = create_product(client, branch.id, "INV-PERM", 5).json()
    barber = make_user(db, role="barber", email="inventory-barber@test.com", branch=branch)
    client_user = make_user(db, role="client", email="inventory-client@test.com")

    app.dependency_overrides[get_current_user] = override_user(barber)
    barber_list = client.get("/api/v1/products/")
    barber_adjust = client.post(
        "/api/v1/inventory/movements",
        json={"product_id": product["id"], "movement_type": "adjustment", "quantity": 8},
    )

    app.dependency_overrides[get_current_user] = override_user(client_user)
    client_list = client.get("/api/v1/products/")

    assert barber_list.status_code == 200
    assert barber_adjust.status_code == 403
    assert client_list.status_code == 403

def test_health_reports_stub_mode(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["llm_mode"] == "stub"


def test_full_order_flow_and_revenue(client):
    # No clients / revenue yet.
    assert client.get("/api/clients").json() == []
    assert client.get("/api/revenue").json()["revenue_rub"] == 0

    # Create a client.
    c = client.post(
        "/api/clients",
        json={"name": "Клиника Улыбка", "industry": "стоматология", "brand_voice": "тёплый"},
    ).json()
    assert c["id"] > 0

    # Create an order — price comes from the catalogue.
    order = client.post(
        "/api/orders",
        json={
            "client_id": c["id"],
            "content_type": "social_post",
            "topic": "Скидка на чистку зубов",
            "brief": "Молодая аудитория, Instagram",
        },
    ).json()
    assert order["status"] == "new"
    assert order["price_rub"] == 1500

    # Pipeline value reflects the not-yet-done order.
    rev = client.get("/api/revenue").json()
    assert rev["pipeline_rub"] == 1500
    assert rev["revenue_rub"] == 0

    # Run the agents.
    deliverable = client.post(f"/api/orders/{order['id']}/run").json()
    assert deliverable["strategy"]
    assert deliverable["final"]

    # Order is done but not yet paid: revenue is 0, the order is outstanding.
    rev = client.get("/api/revenue").json()
    assert rev["revenue_rub"] == 0
    assert rev["orders_done"] == 1
    assert rev["orders_paid"] == 0
    assert rev["pipeline_rub"] == 1500

    # Mark the invoice paid: revenue is booked, nothing outstanding.
    paid = client.post(f"/api/orders/{order['id']}/pay")
    assert paid.status_code == 200
    assert paid.json()["payment_status"] == "paid"
    rev = client.get("/api/revenue").json()
    assert rev["revenue_rub"] == 1500
    assert rev["orders_paid"] == 1
    assert rev["pipeline_rub"] == 0

    # Paying twice is rejected.
    assert client.post(f"/api/orders/{order['id']}/pay").status_code == 409

    # Deliverable is retrievable.
    got = client.get(f"/api/orders/{order['id']}/deliverable")
    assert got.status_code == 200


def test_rerunning_done_order_is_rejected(client):
    c = client.post("/api/clients", json={"name": "Re-run Co"}).json()
    order = client.post(
        "/api/orders",
        json={"client_id": c["id"], "content_type": "article", "topic": "тема"},
    ).json()
    assert client.post(f"/api/orders/{order['id']}/run").status_code == 200

    # Second run must be rejected with 409 (no duplicate deliverable / double revenue).
    again = client.post(f"/api/orders/{order['id']}/run")
    assert again.status_code == 409
    # Revenue is only booked once the invoice is marked paid.
    assert client.get("/api/revenue").json()["revenue_rub"] == 0
    client.post(f"/api/orders/{order['id']}/pay")
    assert client.get("/api/revenue").json()["revenue_rub"] == 6000


def test_pipeline_error_marks_order_failed_and_excludes_from_pipeline(client, monkeypatch):
    import app.routers.orders as orders_mod

    class BoomOrchestrator:
        def __init__(self, *a, **k):
            pass

        def run(self, *a, **k):
            raise RuntimeError("network down")  # not an LLMError

    monkeypatch.setattr(orders_mod, "Orchestrator", BoomOrchestrator)

    c = client.post("/api/clients", json={"name": "Boom Co"}).json()
    order = client.post(
        "/api/orders",
        json={"client_id": c["id"], "content_type": "social_post", "topic": "x"},
    ).json()

    r = client.post(f"/api/orders/{order['id']}/run")
    assert r.status_code == 502  # not a hang / not stuck in_progress

    statuses = {o["id"]: o["status"] for o in client.get("/api/orders").json()}
    assert statuses[order["id"]] == "failed"

    # Failed order must not inflate pipeline (potential) revenue.
    rev = client.get("/api/revenue").json()
    assert rev["pipeline_rub"] == 0
    assert rev["revenue_rub"] == 0


def test_public_intake_creates_client_and_order(client):
    r = client.post(
        "/api/orders/intake",
        json={
            "client_name": "ООО Ромашка",
            "industry": "кофейни",
            "content_type": "newsletter",
            "topic": "Открытие новой точки",
        },
    )
    assert r.status_code == 201
    body = r.json()
    assert body["order_id"] > 0
    assert body["client_id"] > 0
    assert body["price_rub"] == 3500

    # Client and order are now visible to the admin dashboard.
    names = [c["name"] for c in client.get("/api/clients").json()]
    assert "ООО Ромашка" in names
    statuses = {o["id"]: o for o in client.get("/api/orders").json()}
    assert statuses[body["order_id"]]["status"] == "new"
    assert statuses[body["order_id"]]["payment_status"] == "unpaid"

    # Outstanding (not yet paid) shows up as pipeline, not revenue.
    rev = client.get("/api/revenue").json()
    assert rev["revenue_rub"] == 0
    assert rev["pipeline_rub"] == 3500


def test_paying_failed_order_is_rejected(client, monkeypatch):
    import app.routers.orders as orders_mod

    class BoomOrchestrator:
        def __init__(self, *a, **k):
            pass

        def run(self, *a, **k):
            raise RuntimeError("network down")

    monkeypatch.setattr(orders_mod, "Orchestrator", BoomOrchestrator)
    c = client.post("/api/clients", json={"name": "Fail Co"}).json()
    order = client.post(
        "/api/orders",
        json={"client_id": c["id"], "content_type": "article", "topic": "x"},
    ).json()
    assert client.post(f"/api/orders/{order['id']}/run").status_code == 502

    # A failed order cannot be invoiced.
    assert client.post(f"/api/orders/{order['id']}/pay").status_code == 400
    assert client.get("/api/revenue").json()["revenue_rub"] == 0


def test_paying_missing_order_404(client):
    assert client.post("/api/orders/999/pay").status_code == 404


def test_order_for_missing_client_404(client):
    r = client.post(
        "/api/orders",
        json={"client_id": 999, "content_type": "article", "topic": "x"},
    )
    assert r.status_code == 404


def test_pricing_endpoint(client):
    r = client.get("/api/pricing")
    assert r.status_code == 200
    assert set(r.json()) == {"social_post", "article", "newsletter"}

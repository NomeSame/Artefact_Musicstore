def test_home_and_catalogue(client):
    assert client.get("/").status_code==200
    assert "Your music guide" in client.get("/").text
    result=client.get("/api/products?category_id=4").json()
    assert result["products"] and all(p["category_id"]==4 for p in result["products"])
    assert client.get("/api/products?payment=invalid").status_code==422
    assert client.get("/api/products?max_price=-5").status_code==422

def test_preview_uses_real_data_and_exports_it(client):
    response=client.post("/api/chat",json={"message":"Show acoustic guitars under R$1000"})
    assert response.status_code==200
    result=response.json()
    assert result["mode"]=="preview" and result["products"]
    assert result["trace"][0]["name"]=="search_products"
    assert all(p["price_cents"]<=100000 for p in result["products"])
    export=client.get("/api/chat/export")
    assert "Show acoustic guitars under R$1000" in export.text
    assert "preview" in export.text
    assert export.headers["content-disposition"].endswith('"conversation.md"')

def test_selected_product_and_context_validation(client):
    result=client.post("/api/chat",json={"message":"What does this cost with PIX?",
        "context":{"category_id":5,"selected_product_id":81}}).json()
    assert result["products"][0]["product_id"]==81
    assert result["trace"][0]["arguments"]["payment"]=="pix"
    assert client.post("/api/chat",json={"message":"price","context":{
        "category_id":4,"selected_product_id":81}}).status_code==422
    assert client.post("/api/chat",json={"message":"price","context":{
        "selected_product_id":99999}}).status_code==422

def test_order_verification_does_not_leak_customers(client,app):
    result=client.post("/api/chat",json={"message":"Where is order 1?"}).json()
    assert "verification" in result["trace"][0]["result"]["error"]
    assert client.post("/api/orders/verify",json={"order_id":1,"email":"wrong@example.test"}).status_code==403
    catalog=app.state.tools.catalog
    with catalog.connect() as conn:
        email=conn.execute("SELECT c.email FROM customers c JOIN orders o USING(customer_id) WHERE o.order_id=1").fetchone()[0]
    response=client.post("/api/orders/verify",json={"order_id":1,"email":email})
    assert response.status_code==200
    assert "email" not in response.json()["order"]
    result=client.post("/api/chat",json={"message":"Where is order 1?"}).json()
    assert result["trace"][0]["result"]["order"]["order_id"]==1
    client.post("/api/chat/reset",json={})
    result=client.post("/api/chat",json={"message":"Where is order 1?"}).json()
    assert result["trace"][0]["result"]["error"]=="verification_required"

def test_same_origin_and_local_host_boundary(client):
    assert client.post("/api/config",json={},headers={"Origin":"https://evil.example"}).status_code==403
    assert client.get("/api/bootstrap",headers={"host":"evil.example"}).status_code==400
    assert client.post("/api/chat",content="x"*65000).status_code==413

def test_secrets_stay_in_session_and_are_cleared_on_endpoint_change(client):
    result=client.post("/api/config",json={"base_url":"http://localhost:1234/v1",
        "model":"sample","api_key":"test-secret-not-a-real-key"}).json()
    assert result["has_key"] is True
    assert "test-secret-not-a-real-key" not in str(result)
    assert "test-secret-not-a-real-key" not in client.get("/api/bootstrap").text
    changed=client.post("/api/config",json={"base_url":"http://localhost:8080/v1","model":"other"}).json()
    assert changed["has_key"] is False
    assert client.post("/api/config",json={"base_url":"file:///etc/passwd"}).status_code==422

def test_independent_browser_sessions(app):
    from fastapi.testclient import TestClient
    with TestClient(app) as one, TestClient(app) as two:
        one.post("/api/config",json={"base_url":"http://localhost:1234/v1","model":"first","api_key":"private"})
        assert two.get("/api/bootstrap").json()["config"]["mode"]=="preview"


def test_manual_is_the_supplied_pdf(client):
    response=client.get("/api/manual")
    assert response.status_code==200
    assert response.headers["content-type"]=="application/pdf"
    assert response.content.startswith(b"%PDF")

def test_product_page_and_direct_url(client):
    response = client.get("/products/81")
    assert response.status_code == 200
    assert 'id="product-page"' in response.text
    data = client.get("/api/products/81?payment=pix").json()
    assert data["product"]["name"] == "Yamaha C40 Nylon Natural"
    assert data["product"]["price_cents"] == 56991
    assert data["product"]["specs"]["top"] == "Spruce"
    assert {policy["topic"] for policy in data["policies"]} == {"delivery", "returns", "warranty"}
    assert all(policy["sources"] for policy in data["policies"])
    assert client.get("/products/99999").status_code == 404
    assert client.get("/api/products/99999").status_code == 404
    assert client.get("/api/products/81?payment=unknown").status_code == 422


def test_product_question_returns_specifications_instead_of_only_price(client):
    result = client.post("/api/chat", json={
        "message": "What are the materials and technical specifications of this instrument?",
        "context": {"category_id": 5, "selected_product_id": 81},
    }).json()
    assert result["trace"][0]["name"] == "get_product"
    assert result["trace"][0]["arguments"]["focus"] == "specifications"
    assert "Spruce" in result["answer"]
    assert "650mm" in result["answer"]
    assert "The quoted price" not in result["answer"]


def test_product_sound_and_stock_questions_are_distinct(client):
    context = {"category_id": 5, "selected_product_id": 81}
    sound = client.post("/api/chat", json={"message":
        "What sound-related specifications and electronics are recorded for this instrument?",
        "context": context}).json()
    assert sound["trace"][0]["arguments"]["focus"] == "sound"
    assert "Specifications cannot confirm its tone" in sound["answer"]
    assert "Electronics: no" in sound["answer"]
    stock = client.post("/api/chat", json={"message":
        "Is this instrument available, and how many are in stock?", "context": context}).json()
    assert stock["trace"][0]["arguments"]["focus"] == "availability"
    assert "12 units" in stock["answer"]
    assert "The quoted price" not in stock["answer"]

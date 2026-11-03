import pytest
from emporio.domain.pricing import cents, quote

def test_snapshot_is_imported_with_relationships(app):
    catalog = app.state.tools.catalog
    assert len(catalog.search()) == 65
    assert sum(c["count"] for c in catalog.categories()) == 65
    with catalog.connect() as conn:
        assert not conn.execute("PRAGMA foreign_key_check").fetchall()
        assert conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 20
        assert conn.execute("SELECT COUNT(*) FROM promotions WHERE is_active=1").fetchone()[0] == 4

@pytest.mark.parametrize("promotion,payment,expected", [
    (0,"pix",9500),(3,"pix",9500),(10,"pix",9000),
    (10,"card",9000),(0,"card",10000),(10,"unspecified",9000),
])
def test_best_single_discount(promotion,payment,expected):
    assert quote(10000,promotion,payment)["price_cents"] == expected

def test_money_rounding_is_half_up():
    assert cents("599.905") == 59991
    assert quote(59990,0,"pix")["price_cents"] == 56991

def test_actual_budget_availability_and_injection(app):
    catalog=app.state.tools.catalog
    products=catalog.search(category_id=5,max_price=1000,available_only=True,payment="pix")
    assert products
    assert all(p["category_id"]==5 and p["price_cents"]<=100000 and p["available"] for p in products)
    assert catalog.search(query="' OR 1=1 --")==[]
    assert catalog.search(query="Yamáha",category_id=5)
    assert catalog.product(99999) is None

def test_inactive_promotions_are_not_applied(app):
    catalog=app.state.tools.catalog
    with catalog.connect() as conn:
        row=conn.execute("SELECT product_id FROM promotions GROUP BY product_id "
                         "HAVING MAX(is_active)=0 LIMIT 1").fetchone()
    assert row is not None
    assert catalog.product(row[0])["promotion_percent"]==0

def test_tools_validate_inputs_and_scope_orders(app):
    tools=app.state.tools
    assert tools.execute("search_products",{"max_price":-1})["error"]=="invalid_arguments"
    assert tools.execute("search_products",{"arbitrary_sql":"DROP TABLE products"})["error"]=="invalid_arguments"
    assert tools.execute("get_order",{"order_id":1})["error"]=="verification_required"
    assert tools.execute("get_order",{"order_id":2},verified_order=1)["error"]=="verification_required"
    assert tools.execute("get_order",{"order_id":1},verified_order=1)["order"]["order_id"]==1
    product=tools.catalog.product(81)
    wrong=1 if product["category_id"]!=1 else 2
    assert tools.execute("navigate_catalog",{"product_id":81,"category_id":wrong})["error"]=="category_mismatch"
    assert tools.execute("run_shell",{})["error"]=="unknown_tool"

def test_policy_source_pages_and_missing_receipt_date(app):
    result=app.state.tools.execute("lookup_policy",{"topic":"returns"})
    assert result["found"]
    assert {s["page"] for s in result["sources"]}=={4,7}
    assert all(len(s["text"])>100 for s in result["sources"])
    assert "actual receipt date" in result["summary"]


def test_documented_output_contracts_cover_success_and_errors(app):
    import jsonschema
    tools=app.state.tools
    definitions={tool["name"]: tool for tool in tools.catalog_schema()}
    calls=[("search_products",{"category_id":5}),("get_product",{"product_id":81}),
           ("lookup_policy",{"topic":"returns"}),("get_order",{"order_id":1}),
           ("navigate_catalog",{"category_id":4}),("get_product",{"product_id":99999})]
    for name,args in calls:
        jsonschema.validate(tools.execute(name,args),definitions[name]["output_schema"])

def test_product_focus_is_validated_and_overview_preserves_source(app):
    from emporio.agent.engine import render_result
    tools = app.state.tools
    invalid = tools.execute("get_product", {"product_id": 81, "focus": "invent_a_review"})
    assert invalid["error"] == "invalid_arguments"
    result = tools.execute("get_product", {"product_id": 81, "focus": "overview"})
    assert result["focus"] == "overview"
    assert "Classical guitar with a spruce top" in render_result("get_product", result)
    assert result["product"]["description"] in render_result("get_product", result, "pt-BR")

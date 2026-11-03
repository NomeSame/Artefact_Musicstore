import pytest

from emporio.agent.engine import render_result
from emporio.domain.language import DESCRIPTIONS_EN


def test_owner_approved_reassignment_preserves_original_snapshot(app):
    catalog = app.state.tools.catalog
    originals = {int(row["product_id"]): row for row in catalog.rows("products")}
    yamaha, roland = catalog.product(142), catalog.product(144)
    assert yamaha["name"] == "Teclado Arranjador Yamaha 61 Teclas"
    assert yamaha["description"] == originals[144]["description"]
    assert roland["name"] == originals[144]["name"]
    assert roland["description"] == originals[142]["description"]
    assert roland["specs"]["keys"] == "88"
    assert "88" in roland["catalogue_warning"] and "61" not in roland["catalogue_warning"]
    import json
    original_specs = json.loads(originals[144]["specs"])
    assert original_specs["keys"] == "61"
    assert roland["specs"] == {**original_specs, "keys": "88"}
    for product in catalog.search():
        source = originals[product["product_id"]]
        assert product["stock_quantity"] == int(source["stock_quantity"])
        assert product["list_cents"] == round(float(source["price_brl"]) * 100)
        if product["product_id"] not in (142, 144):
            assert product["name"] == source["name"] and product["description"] == source["description"]
    catalog.import_snapshot()
    assert catalog.product(142)["description"] == yamaha["description"]
    assert catalog.product(144)["description"] == roland["description"]
    assert catalog.product(144)["specs"]["keys"] == "88"
    assert catalog.rows("products") == list(originals.values())
    assert originals[142]["name"] == "Teclado Sintetizador Korg Synth 1 Pro"
    assert {p["product_id"] for p in catalog.search(query="Yamaha", category_id=4)} == {142}
    assert {p["product_id"] for p in catalog.search(query="Roland", category_id=4)} == {144}
    assert not catalog.search(query="Korg", category_id=4)


@pytest.mark.parametrize("language", ["en", "pt-BR"])
def test_corrected_api_and_agent_share_descriptions_and_localized_warning(client, app, language):
    catalog = app.state.tools.catalog
    yamaha = client.get(f"/api/products/142?language={language}").json()["product"]
    roland = client.get(f"/api/products/144?language={language}").json()["product"]
    assert yamaha["description_source_product_id"] == 144
    assert roland["description_source_product_id"] == 142
    assert "Yamaha" in yamaha["description"] and "Roland" in roland["description"]
    assert roland["specs"]["keys"] == "88" and yamaha["specs"]["keys"] == "61"
    if language == "en":
        assert yamaha["description"] == DESCRIPTIONS_EN["144"]
        assert roland["description"] == DESCRIPTIONS_EN["142"]
        assert "confirm with the team" in roland["catalogue_warning"]
    else:
        assert "confirme com a equipe" in roland["catalogue_warning"]
    for focus in ("overview", "specifications", "price"):
        answer = render_result("get_product", {"product": catalog.product(144), "focus": focus}, language)
        assert roland["catalogue_warning"] in answer
        if focus == "overview":
            assert roland["description"] in answer
    result = app.state.tools.execute("compare_products", {"product_ids": [142, 144]})
    assert roland["catalogue_warning"] in render_result("compare_products", result, language)

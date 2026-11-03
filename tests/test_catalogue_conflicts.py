import asyncio
import json

import httpx
import pytest

from emporio.agent.engine import Agent, render_result
from emporio.integrations.provider import Provider
from emporio.session.state import Session


@pytest.mark.parametrize("product_id,fields", [
    (135, {"brand", "model", "body"}), (137, {"brand", "model", "strings"}),
    (139, {"brand", "model", "shells"}), (140, {"brand", "model", "shells"}),
])
def test_sql_and_tools_preserve_conflicting_sources_and_expose_uncertainty(app, product_id, fields):
    catalog = app.state.tools.catalog
    original = next(p for p in catalog.rows("products") if int(p["product_id"]) == product_id)
    product = app.state.tools.execute("get_product", {"product_id": product_id})["product"]
    assert product["name"] == original["name"] and product["description"] == original["description"]
    assert product["specs"] == json.loads(original["specs"])
    assert product["catalogue_conflict"] and not product["recommendation_eligible"]
    assert set(product["unconfirmed_fields"]) == fields
    with catalog.connect() as conn:
        stored = conn.execute("SELECT unconfirmed_fields FROM product_conflicts WHERE product_id=?", (product_id,)).fetchone()
        assert set(json.loads(stored[0])) == fields
    catalog.import_snapshot()
    assert catalog.product(product_id)["catalogue_conflict"]


@pytest.mark.parametrize("language", ["en", "pt-BR"])
def test_conflicts_visible_in_api_details_search_and_comparison(client, app, language):
    warning_phrase = "confirm with the team" if language == "en" else "confirme com a equipe"
    for product_id in (135, 137, 139, 140):
        product = client.get(f"/api/products/{product_id}?language={language}").json()["product"]
        assert warning_phrase in product["catalogue_warning"]
        result = app.state.tools.execute("get_product", {"product_id": product_id, "focus": "specifications"})
        assert product["catalogue_warning"] in render_result("get_product", result, language)
    search = app.state.tools.execute("search_products", {"query": "5 cordas", "category_id": 2, "available_only": False})
    assert any(p["product_id"] == 137 for p in search["products"])
    text = render_result("search_products", search, language)
    assert ("not confirmed recommendations" if language == "en" else "não são recomendações confirmadas") in text
    result = app.state.tools.execute("compare_products", {"product_ids": [135, 137], "max_price": 100000})
    assert all(a["checks"]["catalogue_details"] is None for a in result["assessments"])
    text = render_result("compare_products", result, language)
    assert ("unconfirmed" if language == "en" else "não estão confirmados") in text
    assert ("I would start" if language == "en" else "Eu começaria") not in text
    assert warning_phrase in text
    for product_id in (142, 143, 144):
        assert not app.state.tools.catalog.product(product_id)["catalogue_conflict"]
    assert app.state.tools.catalog.product(144)["specs"]["keys"] == "88"


def test_model_receives_uncertainty_and_cannot_replace_visible_warning(app):
    requests = []
    def handler(request):
        payload = json.loads(request.content)
        requests.append(payload)
        if len(requests) == 1:
            message = {"role": "assistant", "content": None, "tool_calls": [{"id": "detail", "type": "function", "function": {
                "name": "get_product", "arguments": json.dumps({"product_id": 137, "focus": "overview"})}}]}
        else:
            message = {"role": "assistant", "content": "Definitely buy this verified five-string bass."}
        return httpx.Response(200, json={"choices": [{"message": message}]})
    agent = Agent(app.state.tools, lambda base, key: Provider(base, key, transport=httpx.MockTransport(handler)))
    result = asyncio.run(agent.reply(Session(base_url="http://model.test/v1", model="test"), "Please look into the Yamaha Bass 3X.", {}))
    assert "unconfirmed_fields" in requests[0]["messages"][0]["content"]
    tool_messages = [m for request in requests for m in request["messages"] if m["role"] == "tool"]
    assert any(json.loads(m["content"]).get("product", {}).get("catalogue_conflict") for m in tool_messages)
    assert "Definitely buy" not in result["answer"]
    assert "not a confirmed four-string or five-string recommendation" in result["answer"]

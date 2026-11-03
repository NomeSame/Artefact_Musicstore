"""Detailed policy coverage and output scope, including weaker tool callers."""
import asyncio
import json
import pytest
from emporio.agent.engine import Agent, render_grounded, render_result
from emporio.domain.policy_details import DETAILS, detail_keys
from emporio.session.state import Session

@pytest.mark.parametrize("question,key,required,excluded", [
    ("Can I pay in 12 credit card installments?", "instalments", "R$100", "PIX"),
    ("Can I combine PIX and card above R$2000?", "mixed_payment", "no 5%", "12 interest"),
    ("Does bank-financed PIX in installments get the discount?", "pix_financing", "full amount", "R$80"),
    ("What PIX discount applies with a promotion?", "pix_discount", "5%", "R$80"),
    ("How long does a refund take?", "refund", "10 business", "7 calendar"),
    ("Does warranty cover falls and unauthorized repairs?", "warranty_exclusions", "falls", "R$"),
    ("Can shipping a large instrument need an individual quote?", "special_shipping", "individual quote", "R$35"),
    ("What are Saturday opening hours?", "hours", "13:00", "PIX"),
    ("Como funciona o PIX parcelado pelo banco?", "pix_financing", "full amount", "R$80"),
    ("Posso combinar PIX e cartão?", "mixed_payment", "no 5%", "12 interest"),
    ("Can I pay 20% by PIX and 80% by card?", "mixed_payment", "no 5%", "12 interest"),
])
def test_specific_policy_keeps_only_requested_details(app, question, key, required, excluded):
    assert detail_keys(question) == [key]
    result = app.state.tools.execute("lookup_policy", {"topic": DETAILS[key][0], "question": question})
    assert result["focuses"] == [key]
    assert required in render_result("lookup_policy", result)
    assert excluded not in render_result("lookup_policy", result)
    assert render_result("lookup_policy", result, "pt-BR") == DETAILS[key][3]
    assert {s["page"] for s in result["sources"]} == set(DETAILS[key][1])
    for p in app.state.tools.catalog.search(limit=100):
        product = app.state.tools.execute("get_product", {"product_id": p["product_id"], "focus": "specifications"})
        for language in ("en", "pt-BR"):
            assert render_grounded([{"name": "get_product", "result": product},
                                    {"name": "lookup_policy", "result": result}], question, language) == render_result("lookup_policy", result, language)

def test_weak_model_topic_and_extra_lookup_do_not_expand_answer(app):
    class Model:
        async def complete(self, model, messages, tools):
            if messages[-1]["role"] == "user":
                return {"tool_calls": [{"id": str(i), "type": "function", "function": {
                    "name": name, "arguments": json.dumps(args)}} for i,(name,args) in enumerate([
                        ("lookup_policy", {"topic": "payments", "question": "Tell me everything"}),
                        ("get_product", {"product_id": 81, "focus": "specifications"}),
                        ("lookup_policy", {"topic": "delivery"})])]}
            return {"content": "Also here are all prices and shipping details."}
    session = Session(base_url="http://test/v1", model="weak")
    result = asyncio.run(Agent(app.state.tools, lambda *a: Model()).reply(session, "Can I pay in 12 installments?", {}))
    assert result["answer"] == DETAILS["instalments"][2]
    assert "Yamaha" not in result["answer"]
    assert result["products"] == []

def test_partial_pix_never_gets_full_pix_quote(app):
    class Model:
        async def complete(self, model, messages, tools):
            if messages[-1]["role"] == "user":
                return {"tool_calls": [{"id":"p","type":"function","function":{
                    "name":"get_product","arguments":'{"product_id":81,"payment":"pix"}'}}]}
            return {"content":"done"}
    result=asyncio.run(Agent(app.state.tools,lambda *a:Model()).reply(
        Session(base_url="http://test/v1",model="weak"), "What is the price if I split payment between PIX and card?", {}))
    product=result["trace"][0]["result"]["product"]
    assert product["payment"] == "card"
    assert product["discount_source"] != "pix"

def test_known_policy_question_works_when_model_omits_tool(app):
    class Model:
        async def complete(self, *args):
            return {"content":"Here is a long, unverified answer about every store policy."}
    reply=asyncio.run(Agent(app.state.tools,lambda *a:Model()).reply(
        Session(base_url="http://test/v1",model="weak"), "How long does a refund take?", {}))
    assert reply["answer"] == DETAILS["refund"][2]
    assert reply["trace"][0]["name"] == "lookup_policy"

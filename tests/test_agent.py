import asyncio
import json
import httpx
import pytest
from emporio.agent.engine import Agent
from emporio.integrations.provider import Provider, ProviderError
from emporio.session.state import Session

def test_model_tool_loop_and_deterministic_facts(app):
    requests=[]
    def handler(request):
        payload=json.loads(request.content);requests.append(payload)
        if len(requests)==1:
            return httpx.Response(200,json={"choices":[{"message":{"role":"assistant","content":None,
                "tool_calls":[{"id":"call1","type":"function","function":{"name":"get_product",
                "arguments":json.dumps({"product_id":81,"payment":"pix"})}}]}}]})
        assert payload["messages"][-1]["role"]=="tool"
        return httpx.Response(200,json={"choices":[{"message":{"role":"assistant",
            "content":"The price is R$999999999.00"}}]})
    transport=httpx.MockTransport(handler)
    agent=Agent(app.state.tools,lambda base,key:Provider(base,key,transport=transport))
    session=Session(base_url="http://model.test/v1",model="reference")
    # An open-ended lookup still exercises a real follow-up model request.
    # Explicit price requests now finish after the initial model/tool round.
    result=asyncio.run(agent.reply(session,"Please look into the Yamaha C40 with PIX.",{}))
    assert len(requests)==2
    assert result["mode"]=="model"
    assert result["products"][0]["product_id"]==81
    assert "999999999" not in result["answer"]
    assert "569.91" in result["answer"]

@pytest.mark.parametrize("status",[401,404,429,500])
def test_provider_errors_do_not_echo_credentials(status):
    transport=httpx.MockTransport(lambda _:httpx.Response(status,json={"error":"private-token"}))
    provider=Provider("http://model.test/v1","private-token",transport)
    with pytest.raises(ProviderError) as caught:
        asyncio.run(provider.models())
    assert "private-token" not in str(caught.value)

def test_bounded_tool_loop(app):
    class Looper:
        async def complete(self,*args):
            return {"role":"assistant","tool_calls":[{"id":"loop","type":"function","function":{
                "name":"get_product","arguments":'{"product_id":81}'}}]}
    agent=Agent(app.state.tools,lambda *args:Looper())
    with pytest.raises(ProviderError,match="six turns"):
        asyncio.run(agent.reply(Session(base_url="http://model.test/v1",model="loop"),"hello",{}))

def test_malformed_tool_call_fails_cleanly(app):
    class Broken:
        async def complete(self,*args):
            return {"tool_calls":[{"function":{"arguments":"not json","name":"get_product"}}]}
    with pytest.raises(ProviderError,match="malformed"):
        asyncio.run(Agent(app.state.tools,lambda *args:Broken()).reply(
            Session(base_url="http://model.test/v1",model="broken"),"hello",{}))


def test_ungrounded_model_facts_are_not_displayed(app):
    class Ungrounded:
        async def complete(self,*args):
            return {"content":"The Yamaha costs R$999999 and shipping is free."}
    agent=Agent(app.state.tools,lambda *args:Ungrounded())
    result=asyncio.run(agent.reply(Session(base_url="http://model.test/v1",model="fake"),"Price?",{}))
    assert "999999" not in result["answer"]
    assert "look up" in result["answer"]
    assert result["products"]==[]


@pytest.mark.parametrize("with_history", [False, True])
def test_strict_template_accepts_context_and_tool_followup(app, with_history):
    calls = []
    def handler(request):
        payload = json.loads(request.content)
        messages = payload["messages"]
        # Reproduce the actual server restriction, for initial and follow-up calls.
        if [i for i, m in enumerate(messages) if m["role"] == "system"] != [0]:
            return httpx.Response(500, json={"error": {
                "message": "System message must be at the beginning."}})
        assert '"category_id": 5' in messages[0]["content"]
        assert '"selected_product_id": 81' in messages[0]["content"]
        assert "Verified order ID: 1" in messages[0]["content"]
        if with_history:
            assert messages[1:3] == [
                {"role": "user", "content": "hey"},
                {"role": "assistant", "content": "How can I help?"}]
        calls.append(payload)
        if len(calls) == 1:
            return httpx.Response(200, json={"choices": [{"message": {
                "role": "assistant", "content": None, "tool_calls": [{
                    "id": "price", "type": "function", "function": {
                        "name": "get_product",
                        "arguments": '{"product_id":81,"payment":"pix"}'}}]}}]})
        assert messages[-1]["role"] == "tool"
        return httpx.Response(200, json={"choices": [{"message": {
            "role": "assistant", "content": "Done."}}]})
    history = ([{"role": "user", "content": "hey"},
                {"role": "assistant", "content": "How can I help?"}] if with_history else [])
    session = Session(base_url="http://model.test/v1", model="strict",
                      history=history.copy(), verified_order=1)
    transport = httpx.MockTransport(handler)
    agent = Agent(app.state.tools, lambda base, key: Provider(base, key, transport))
    result = asyncio.run(agent.reply(session, "Please look into this instrument with PIX.",
        {"category_id": 5, "selected_product_id": 81}))
    assert len(calls) == 2
    assert result["products"][0]["product_id"] == 81
    assert "569.91" in result["answer"]
    assert all(m["role"] != "system" for m in session.history)

@pytest.mark.parametrize("batched", [True, False])
def test_duplicate_read_calls_are_reused_and_rendered_once(app, monkeypatch, batched):
    executions = []
    original = app.state.tools.execute
    def counted(name, args, verified_order=None):
        executions.append((name, args.copy()))
        return original(name, args, verified_order)
    monkeypatch.setattr(app.state.tools, "execute", counted)
    def call(identity, reverse=False):
        args = {"payment": "pix", "product_id": 81} if reverse else {"product_id": 81, "payment": "pix"}
        return {"id": identity, "type": "function", "function": {
            "name": "get_product", "arguments": json.dumps(args)}}
    class Repeating:
        def __init__(self):
            self.turn = 0
        async def complete(self, *args):
            self.turn += 1
            if self.turn == 1:
                return {"tool_calls": [call("first"), call("repeat", True)] if batched else [call("first")]}
            if self.turn == 2 and not batched:
                return {"tool_calls": [call("repeat", True)]}
            return {"content": "Done."}
    agent = Agent(app.state.tools, lambda *args: Repeating())
    session = Session(base_url="http://model.test/v1", model="repeating")
    first = asyncio.run(agent.reply(session, "PIX price?", {}))
    assert len(executions) == 1
    assert first["answer"].count("The quoted price") == 1
    assert len(first["products"]) == 1
    assert [turn["cached"] for turn in first["trace"]] == [False, True]
    with app.state.tools.catalog.connect() as conn, conn:
        conn.execute("UPDATE products SET price_cents=69990 WHERE product_id=81")
    second = asyncio.run(agent.reply(session, "Check the price again.", {}))
    assert len(executions) == 2
    assert "664.91" in second["answer"]
    assert [turn["cached"] for turn in second["trace"]] == [False, True]


def test_distinct_payment_quotes_are_not_suppressed(app):
    from emporio.agent.engine import render_grounded
    tools = app.state.tools
    traces = [{"name": "get_product", "result": tools.execute("get_product",
        {"product_id": 81, "payment": payment})} for payment in ["card", "pix"]]
    text = render_grounded(traces)
    assert "599.90" in text and "569.91" in text
    assert text.count("The quoted price") == 2


@pytest.mark.parametrize("count,phrase", [(1, "1 matching instrument."), (2, "2 matching instruments.")])
def test_catalogue_answer_uses_singular_or_plural(count, phrase):
    from emporio.agent.engine import render_result
    answer = render_result("search_products", {"products": [{}] * count, "count": count})
    assert phrase in answer
    assert ("The card below uses" if count == 1 else "The cards below use") in answer


def test_greeting_is_warm_without_displaying_ungrounded_model_claims(app):
    class UnreliableGreeting:
        async def complete(self, *args):
            return {"content": "Hi, everything is half price today!"}
    agent = Agent(app.state.tools, lambda *args: UnreliableGreeting())
    session = Session(base_url="http://model.test/v1", model="greeting")
    first = asyncio.run(agent.reply(session, "hey!", {}))
    assert "welcome to Empório da Música" in first["answer"]
    assert "Happy to help" in first["answer"]
    assert "half price" not in first["answer"]
    second = asyncio.run(agent.reply(session, "hello", {}))
    assert "Hi again!" in second["answer"]
    preview = asyncio.run(agent.reply(Session(), "hey", {}))
    assert "not a connected AI model" in preview["answer"]


@pytest.mark.parametrize("message,show_overview", [
    ("What warranty information is available for this instrument?", False),
    ("Give me an overview and the warranty information for this instrument.", True),
])
def test_policy_reply_omits_context_overview_unless_requested(app, message, show_overview):
    tools = app.state.tools
    calls = [{"name": "lookup_policy", "result": tools.execute("lookup_policy", {"topic": "warranty"})},
        {"name": "get_product", "result": tools.execute("get_product", {"product_id": 145, "focus": "overview"})}]
    from emporio.agent.engine import render_grounded
    answer = render_grounded(calls, message)
    assert "90 days" in answer
    assert ("Recorded details" in answer) is show_overview
    assert ("Fender Stratocaster electric guitar" in answer) is show_overview


def test_focused_product_reply_omits_redundant_search_count(app):
    from emporio.agent.engine import render_grounded
    tools = app.state.tools
    product = tools.execute("get_product", {"product_id": 145, "focus": "sound"})
    search = {"products": [product["product"]], "count": 1}
    answer = render_grounded([{"name": "search_products", "result": search},
        {"name": "get_product", "result": product}], "What sound-related specifications are recorded?")
    assert "matching instrument" not in answer
    assert "Mahogany" not in answer  # Fender source must not inherit another product's details.
    assert "Please, ask the team about a listening demo or trying it in person." in answer


def test_search_results_for_other_products_are_not_hidden(app):
    from emporio.agent.engine import render_grounded
    tools = app.state.tools
    product = tools.execute("get_product", {"product_id": 145, "focus": "sound"})
    search = {"products": [product["product"], tools.catalog.product(81)], "count": 2}
    answer = render_grounded([{"name": "search_products", "result": search},
        {"name": "get_product", "result": product}])
    assert "2 matching instruments" in answer

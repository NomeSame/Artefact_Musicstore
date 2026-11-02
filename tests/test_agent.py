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
    result=asyncio.run(agent.reply(session,"Price of Yamaha C40 with PIX?",{}))
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
    result = asyncio.run(agent.reply(session, "What does this cost with PIX?",
        {"category_id": 5, "selected_product_id": 81}))
    assert len(calls) == 2
    assert result["products"][0]["product_id"] == 81
    assert "569.91" in result["answer"]
    assert all(m["role"] != "system" for m in session.history)

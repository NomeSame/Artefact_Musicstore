"""Regressions reproduced by the live functional acceptance, without expensive inference."""
import asyncio
import json
import pytest
from emporio.agent.engine import Agent
from emporio.session.state import Session


class WrongSearch:
    def __init__(self):self.calls=0
    async def complete(self,*args):
        self.calls+=1
        if self.calls>1:raise AssertionError('Known requests must not loop through stale searches')
        return {'tool_calls':[{'id':'wrong','type':'function','function':{
            'name':'search_products','arguments':'{"query":"","category_id":1}'}}]}


def reply(app,message,context=None,language='en',verified=None):
    model=WrongSearch();session=Session(base_url='http://test/v1',model='weak',language=language,verified_order=verified)
    result=asyncio.run(Agent(app.state.tools,lambda *a:model).reply(session,message,context or {}))
    return result,model


def test_named_product_and_pix_override_stale_ui_and_wrong_model_category(app):
    result,model=reply(app,'What is the Yamaha F310 price with PIX?',{'selected_product_id':81,'payment':'pix'})
    assert [p['product_id'] for p in result['products']]==[87]
    assert result['products'][0]['price_cents']==66491
    assert '664.91' in result['answer'] and '569.91' not in result['answer']
    assert model.calls==1


def test_source_budget_category_and_brand_cannot_be_dropped(app):
    result,_=reply(app,'Which Yamaha acoustic guitars are available under R$1000?')
    assert result['products']
    assert all(p['category_id']==5 and p['available'] and p['price_cents']<=100000 and 'Yamaha' in p['name'] for p in result['products'])
    assert all(p['product_id']<131 for p in result['products'])


@pytest.mark.parametrize('id,status',[(96,'out of stock'),(136,'discontinued'),(130,'coming soon')])
def test_current_selection_not_old_conversation_product(app,id,status):
    result,_=reply(app,'Is this instrument available to buy?',{'selected_product_id':id})
    assert [p['product_id'] for p in result['products']]==[id]
    assert result['products'][0]['available'] is False
    assert status in result['answer']


def test_mixed_payment_returns_product_quote_and_conditional_policy(app):
    result,_=reply(app,'What is the price if I split payment between PIX and card?',{'selected_product_id':90,'payment':'pix'})
    assert result['products'][0]['price_cents']==196718
    assert result['products'][0]['payment']=='card'
    assert '1,967.18' in result['answer'] and 'no 5%' in result['answer']


@pytest.mark.parametrize('language,required',[('en','not recorded'),('pt-BR','não está registrado')])
def test_weight_gap_answer_is_explicit_and_narrow(app,language,required):
    result,_=reply(app,'How much does this instrument weigh?',{'selected_product_id':81},language)
    assert required in result['answer']
    assert 'Spruce' not in result['answer'] and 'R$' not in result['answer']


@pytest.mark.parametrize('language,required',[('en','instruments only'),('pt-BR','apenas instrumentos')])
def test_accessory_scope_comes_from_manual(app,language,required):
    result,_=reply(app,'Do you sell cables or amplifiers?',language=language)
    assert required in result['answer'] and not result['products']
    assert {s['page'] for s in result['sources']}=={2,6}


def test_ambiguous_price_asks_for_product_without_model_guess(app):
    result,model=reply(app,'What does it cost?',{'category_id':5,'visible_product_ids':[81,87]})
    assert 'Which instrument' in result['answer'] and not result['products']
    assert model.calls==0


def test_verified_order_is_answered_even_if_model_omits_order_tool(app):
    result,_=reply(app,'What is the status of order 1?',verified=1)
    assert 'delivered' in result['answer'] and 'BRAB1234567BR' in result['answer']
    assert not result['products']


def test_actual_requested_order_still_needs_its_own_verification(app):
    result,_=reply(app,'What is the status of order 2?',verified=1)
    assert 'lookup dialog' in result['answer']
    assert 'BRCX9876543BR' not in result['answer'] and 'BRAB1234567BR' not in result['answer']


def test_inactive_promotion_answer_excludes_it_and_quotes_pix(app):
    result,_=reply(app,'What is the PIX price? Does an inactive promotion apply?',{'selected_product_id':102,'payment':'pix'})
    assert '3,704.05' in result['answer'] and 'Inactive' in result['answer']


def test_other_instrument_category_never_quotes_current_guitar(app):
    result,model=reply(app,'What is the price of a violin?',{'selected_product_id':81})
    assert 'Which instrument' in result['answer'] and not result['products']
    assert model.calls==0


def test_short_how_much_question_uses_current_product(app):
    result,_=reply(app,'How much is it with PIX?',{'selected_product_id':81})
    assert '569.91' in result['answer']


def test_selected_single_product_does_not_reuse_old_comparison_for_weight(app):
    model=WrongSearch()
    session=Session(base_url='http://test/v1',model='weak',advice={'ids':[98,115],'preferences':{}})
    result=asyncio.run(Agent(app.state.tools,lambda *a:model).reply(session,
        'How much does this instrument weigh?',{'selected_product_id':81}))
    assert 'Yamaha C40' in result['answer'] and 'NTX1' not in result['answer']


def test_resolved_availability_does_not_wait_for_model(app):
    class Model:
        async def complete(self,*args):
            raise AssertionError('A resolved stock/status gate needs no model reasoning')
    result=asyncio.run(Agent(app.state.tools,lambda *a:Model()).reply(
        Session(base_url='http://test/v1',model='weak'),'Can I buy this discontinued instrument?',{'selected_product_id':136}))
    assert 'discontinued' in result['answer'] and not result['products'][0]['available']

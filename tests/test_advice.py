"""Grounded comparisons, ambiguity, explicit preferences and session isolation."""
import asyncio
import json
import pytest
from emporio.agent.engine import Agent
from emporio.domain.advice import compare, render_comparison, preferences_from_message, named_products
from emporio.session.state import Session


def test_comparison_explains_differences_and_asks_without_inventing_winner(app):
    result=app.state.tools.execute('compare_products',{'product_ids':[81,87]})
    text=render_comparison(result)
    assert 'nylon' in text and 'steel' in text
    assert '100.00 less' in text and 'maximum budget' in text
    assert 'do not yet justify' in text and 'cannot confirm tone' in text
    assert len(result['products'])==2


@pytest.mark.parametrize('language',['en','pt-BR'])
def test_budget_and_strings_support_explained_candidate(app, language):
    result=compare(app.state.tools.catalog,[81,87],max_price=650,string_type='nylon',beginner=True)
    assert [a['checks']['budget'] for a in result['assessments']]==[True,False]
    assert [a['checks']['string_type'] for a in result['assessments']]==[True,False]
    text=render_comparison(result,language)
    assert 'Yamaha C40' in text
    assert ('only one' if language=='en' else 'é o único') in text
    assert ('beginner' if language=='en' else 'iniciante') in text


def test_unknown_electronics_not_treated_as_absent_and_stock_blocks_recommendation(app):
    result=compare(app.state.tools.catalog,[131,145],electronics=True)
    assert all(a['checks']['electronics'] is None for a in result['assessments'])
    assert 'not recorded' in render_comparison(result)
    result=compare(app.state.tools.catalog,[81,87],max_price=10000)
    result['assessments'][0]['checks']['available']=False
    assert 'Yamaha F310' in render_comparison(result)
    assert 'Yamaha C40 Nylon Natural is the only' not in render_comparison(result)


@pytest.mark.parametrize('question,expected',[
    ('My budget is R$ 1,000.50 and I prefer nylon strings.',{'max_price':1000.50,'string_type':'nylon'}),
    ('Meu orçamento é R$ 1.000,50 e prefiro cordas de aço.',{'max_price':1000.50,'string_type':'steel'}),
    ('I am a beginner and want to play at home.',{'beginner':True,'use_case':'home'}),
    ('I need built-in electronics.',{'electronics':True}),
    ("I don't need amplification.",{'electronics':None}),
    ("I don't want nylon strings.",{}),
    ('I want an instrument without electronics.',{'electronics':False}),
    ('No budget limit and no string preference.',{'max_price':None,'string_type':None}),
    ('I prefer nylon over steel.',{'string_type':'nylon'}),
    ('I am not a beginner.',{'beginner':False}),
])
def test_only_explicit_preferences_enter_state(question,expected):
    assert preferences_from_message(question)==expected


def test_names_not_arbitrary_catalogue_words(app):
    products=app.state.tools.catalog.search(limit=100)
    assert named_products('Compare C40 and F310',products)==[81,87]
    assert named_products('Compare 81 and 87',products)==[81,87]
    assert named_products('Compare product 81 and product 99999',products)==[81,99999]
    assert named_products('I want to play in a studio with a natural sound.',products)==[]


def test_preview_followups_revise_explicit_preferences_and_keep_language(client,app):
    first=client.post('/api/chat',json={'message':'Compare C40 and F310. Which is better for me?'}).json()
    assert 'maximum budget' in first['answer']
    second=client.post('/api/chat',json={'message':'My budget is R$650 and I prefer nylon strings.'}).json()
    assert 'Yamaha C40' in second['answer'] and 'only one' in second['answer']
    third=client.post('/api/chat',json={'message':'Quero cordas de aço e meu orçamento é R$800.','language':'pt-BR'}).json()
    assert 'Yamaha F310' in third['answer'] and 'é o único' in third['answer']
    fourth=client.post('/api/chat',json={'message':'Qual é mais confortável?'}).json()
    assert 'não informa ação' in fourth['answer'] and 'R$' not in fourth['answer']
    assert fourth['products']==[]
    session=next(iter(app.state.sessions.items.values()))
    assert session.advice['preferences']['string_type']=='steel'
    client.post('/api/chat/reset',json={})
    assert not session.advice and not session.last_product_ids


def test_ambiguity_does_not_choose_first_two_from_category(client):
    reply=client.post('/api/chat',json={'message':'Which of these two guitars is better?',
        'context':{'category_id':5,'visible_product_ids':[81,82,83,87]}}).json()
    assert 'Which two or three models' in reply['answer']
    assert not reply['products'] and not reply['trace']


def test_weaker_model_cannot_invent_ids_or_preferences(app):
    class Model:
        async def complete(self,model,messages,tools):
            if messages[-1]['role']=='user':
                return {'tool_calls':[{'id':'compare','type':'function','function':{
                    'name':'compare_products','arguments':json.dumps({'product_ids':[131,145],'max_price':999999,'electronics':True})}}]}
            return {'content':'The Fender has objectively superior tone and suits rock best.'}
    session=Session(base_url='http://test/v1',model='weak')
    reply=asyncio.run(Agent(app.state.tools,lambda *a:Model()).reply(session,
        'Compare C40 and F310. My budget is R$650 and I prefer nylon.',{}))
    assert [p['product_id'] for p in reply['products']]==[81,87]
    assert session.advice['preferences']=={'max_price':650,'string_type':'nylon'}
    assert 'superior' not in reply['answer'] and 'Yamaha C40' in reply['answer']


def test_omitted_comparison_tool_is_safely_completed(app):
    class Model:
        async def complete(self,*args):return {'content':'Buy whichever one I like.'}
    session=Session(base_url='http://test/v1',model='weak')
    reply=asyncio.run(Agent(app.state.tools,lambda *a:Model()).reply(session,'Compare C40 and F310',{}))
    assert reply['trace'][0]['name']=='compare_products'
    assert '100.00 less' in reply['answer']


@pytest.mark.parametrize('ids',[[81,81],[81,99999]])
def test_invalid_comparisons_do_not_substitute_other_products(app,ids):
    result=app.state.tools.execute('compare_products',{'product_ids':ids})
    assert result.get('error') and not result.get('products')


def test_advice_is_session_scoped_and_config_reset_clears_it(app):
    from fastapi.testclient import TestClient
    with TestClient(app) as a, TestClient(app) as b:
        a.post('/api/chat',json={'message':'Compare C40 and F310'})
        other=b.post('/api/chat',json={'message':'Which is better for me?'}).json()
        assert 'Which two or three' in other['answer'] and not other['products']
        a.post('/api/config',json={'base_url':'','model':''})
        again=a.post('/api/chat',json={'message':'Which is better for me?'}).json()
        assert 'Which two or three' in again['answer']


def test_comparison_mixed_payment_never_gets_pix_rate(client):
    reply=client.post('/api/chat',json={'message':'Compare C40 and F310. I split payment between PIX and card.',
        'context':{'payment':'pix'}}).json()
    product=reply['trace'][0]['result']['products'][0]
    assert product['payment']=='card' and product['discount_source']!='pix'


def test_new_search_does_not_reuse_old_comparison_pair(client):
    client.post('/api/chat',json={'message':'Compare C40 and F310'})
    client.post('/api/chat',json={'message':'Show electric guitars'})
    result=client.post('/api/chat',json={'message':'Compare these guitars'}).json()
    assert 'Which two or three' in result['answer']


def test_budget_filtered_search_loop_cannot_hide_expensive_comparison_model(app):
    class Model:
        calls=0
        async def complete(self,*args):
            self.calls+=1
            return {'tool_calls':[{'id':'search','type':'function','function':{
                'name':'search_products','arguments':'{"query":"Yamaha NTX1","max_price":3000}'}}]}
    model=Model()
    reply=asyncio.run(Agent(app.state.tools,lambda *a:model).reply(
        Session(base_url='http://test/v1',model='weak'),
        'Compare Yamaha NTX1 and Takamine GC1CE. My budget is R$3000 and I prefer nylon.',{}))
    assert model.calls==1
    assert [p['product_id'] for p in reply['products']]==[98,115]
    assert 'exceeds your budget' in reply['answer']


def test_three_previous_models_do_not_resolve_which_two(client):
    client.post('/api/chat',json={'message':'Compare C40, F310 and C70'})
    reply=client.post('/api/chat',json={'message':'Which of these two is better?'}).json()
    assert 'Which two or three' in reply['answer'] and not reply['products']


def test_unknown_id_does_not_show_unrelated_search_cards(app):
    class Model:
        async def complete(self,*args):
            return {'tool_calls':[{'id':'s','type':'function','function':{
                'name':'search_products','arguments':'{"category_id":1}'}}]}
    reply=asyncio.run(Agent(app.state.tools,lambda *a:Model()).reply(
        Session(base_url='http://test/v1',model='weak'),'Compare product 81 and product 99999',{}))
    assert not reply['products'] and 'Please choose' in reply['answer']


def test_known_missing_evidence_followup_does_not_wait_for_model(app):
    class Model:
        async def complete(self,*args):
            raise AssertionError('Known missing catalogue evidence needs no new inference')
    session=Session(base_url='http://test/v1',model='weak',advice={'ids':[81,87],'preferences':{}})
    reply=asyncio.run(Agent(app.state.tools,lambda *a:Model()).reply(session,'Which one is more comfortable?',{}))
    assert 'cannot confirm which is easier' in reply['answer'] and not reply['products']


def test_comparison_restricts_tools_and_labels_connection_fallback(app):
    from emporio.integrations.provider import ProviderError
    class Model:
        async def complete(self,model,messages,tools):
            assert [t['function']['name'] for t in tools]==['compare_products']
            raise ProviderError('The model endpoint timed out.')
    reply=asyncio.run(Agent(app.state.tools,lambda *a:Model()).reply(
        Session(base_url='http://test/v1',model='weak'),'Compare C40 and F310',{}))
    assert reply['model_error']=='The model endpoint timed out.'
    assert 'catalogue-only comparison' in reply['answer']
    assert [p['product_id'] for p in reply['products']]==[81,87]


def test_best_question_reuses_pair_but_best_pix_question_stays_policy(client):
    client.post('/api/chat',json={'message':'Compare C40 and F310'})
    best=client.post('/api/chat',json={'message':'Which is best for me?'}).json()
    assert 'maximum budget' in best['answer']
    policy=client.post('/api/chat',json={'message':'What is the best PIX discount with a promotion?'}).json()
    assert '5%' in policy['answer'] and not policy['products']

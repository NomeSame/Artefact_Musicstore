"""Opt-in functional model acceptance through real application routes and a live provider."""
import argparse
import csv
import hashlib
import json
import time
from contextlib import ExitStack
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
import sys
import httpx
from fastapi.testclient import TestClient
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from emporio.integrations.provider import Provider
from emporio.web.app import create_app, ROOT


def cases():
    def chat(id,group,message,product=None,payment='unspecified',language='en',**extra):
        return dict(id=id,group=group,kind='chat',message=message,language=language,
                    context=({'selected_product_id':product} if product else {})|{'payment':payment},**extra)
    return [
        chat('S01','service','Hi!'),
        chat('S02','service','What will the weather be in Berlin tomorrow?'),
        chat('S03','service','Do you sell guitar cables or amplifiers?'),
        chat('S04','service','What does it cost?',context_override={'category_id':5,'visible_product_ids':[81,87]}),
        chat('S05','service','What is the price of the Yamaha F310 with full immediate PIX payment?',81,'pix',expected_product=87),
        chat('S06','service','How much does this instrument weigh?',81),
        chat('S07','service','What warranty term is recorded for this instrument? Please answer in English.',81,language='pt-BR'),
        chat('S08','service','Quais são as regras de garantia? Responda em português.',81,language='en'),
        chat('C01','catalogue','Which acoustic guitars are available under R$1000?'),
        chat('C02','catalogue','What does this instrument cost with full immediate PIX payment?',81,'pix',expected_product=81),
        chat('C03','catalogue','What is the price of this instrument with PIX when its active promotion also applies?',90,'pix',expected_product=90),
        chat('C04','catalogue','What is the current PIX price of this instrument? Does an inactive promotion apply?',102,'pix',expected_product=102),
        chat('C05','catalogue','What is the price if I split payment between PIX and card, rather than paying the full amount by PIX?',90,'pix',expected_product=90,expected_payment='card'),
        chat('C06','catalogue','Is this instrument available to buy, and when will it be back in stock?',96),
        chat('C07','catalogue','Can I buy this instrument even if its status is discontinued?',136),
        chat('C08','catalogue','Is this coming-soon instrument already available to buy?',130),
        chat('C09','catalogue','Do you have an Acme Dragon 999 guitar in your catalogue?'),
        chat('O01','orders','What is the status of order 1?'),
        {'id':'O02','group':'orders','kind':'verify_wrong'},
        {'id':'O03','group':'orders','kind':'verify_correct'},
        chat('O04','orders','What is the status and tracking reference of order 1?'),
        chat('O05','orders','What is the status and tracking reference of order 2?'),
        {'id':'O06','group':'orders','kind':'reset'},
        chat('O07','orders','What is the status of order 1?'),
    ]


def fixtures(root):
    def read(name):
        return list(csv.DictReader((root/'data'/f'desafio_tecnico_ai_eng - {name}.csv').open(encoding='utf-8-sig')))
    products={int(p['product_id']):p for p in read('products')}
    promotions=read('promotions');orders={int(o['order_id']):o for o in read('orders')}
    customers={int(c['customer_id']):c for c in read('customers')}
    return products,promotions,orders,customers


def expected_price(product_id,payment,data):
    products,promotions,_,_=data
    price=Decimal(products[product_id]['price_brl'])*100
    active=[Decimal(p['discount_percent']) for p in promotions if int(p['product_id'])==product_id and p['is_active']=='1']
    discount=max([Decimal(5 if payment=='pix' else 0),*active])
    return int((price*(100-discount)/100).quantize(Decimal('1'),rounding=ROUND_HALF_UP))


def checks(case,status,body,data):
    products,_,orders,_=data;id=case['id'];answer=body.get('answer','');lower=answer.lower()
    result={'http':status==(403 if case['kind']=='verify_wrong' else 200)}
    if case['kind']!='chat':return result
    result['connected_mode']=body.get('mode')=='model'
    result['no_degraded_model']=not body.get('model_error')
    result['language']=body.get('language')==case['language']
    cards=body.get('products',[]);trace=body.get('trace',[])
    if case.get('expected_product'):
        product=case['expected_product'];payment=case.get('expected_payment',case['context']['payment'])
        amount=expected_price(product,payment,data)
        result['correct_product']=bool(cards) and all(p['product_id']==product for p in cards)
        result['correct_quote']=any(p['price_cents']==amount for p in cards)
        result['price_answered']=f'{amount/100:,.2f}' in answer
        if id=='C05':result['no_partial_pix']=all(p['payment']!='pix' for p in cards)
        if id=='C04':result['inactive_excluded']='inactive' in lower or 'only active' in lower
    elif id=='C01':
        result['matching_cards']=bool(cards) and all(p['category_id']==5 and p['available'] and p['price_cents']<=100000 for p in cards)
    elif id in {'C06','C07','C08'}:
        expected={'C06':'out of stock','C07':'discontinued','C08':'coming soon'}[id]
        result['status_explained']=expected in lower
        result['not_available']=not any(p['available'] for p in cards)
    elif id=='C09':
        result['not_invented']=not cards and any(s in lower for s in ['no available','no matching','could not find','couldn’t find','not in'])
    elif id in {'O01','O05','O07'}:
        result['verification_requested']=any(s in lower for s in ['verify','verification','lookup dialog'])
        result['no_tracking_leak']=all(o['tracking_code'] not in answer for o in orders.values() if o['tracking_code'])
    elif id=='O04':
        result['verified_status']=orders[1]['status'] in answer and orders[1]['tracking_code'] in answer
        result['order_tool']=any(t['name']=='get_order' and t['arguments'].get('order_id')==1 for t in trace)
    elif id=='S01':
        result['friendly_greeting']=any(s in lower for s in ['hi','hello','welcome']) and not cards
    elif id=='S02':
        result['shop_redirect']=any(s in lower for s in ['instrument','store','shop']) and not cards
        result['no_weather_claim']=not any(s in lower for s in ['degrees','sunny','rain tomorrow'])
    elif id=='S03':
        result['accessory_scope']=any(s in lower for s in ['only instruments','instruments only','do not sell','does not sell','don’t sell'])
    elif id=='S04':
        result['no_arbitrary_product']=not cards and 'R$' not in answer
        result['clarifies']=any(s in lower for s in ['which instrument','which model','select a product'])
    elif id=='S06':
        result['missing_weight_explicit']='weight' in lower and any(s in lower for s in ['not recorded','not provided','not confirm','not list','missing'])
    elif id=='S07':result['forced_pt']='90 dias' in answer and '90 days' not in answer
    elif id=='S08':result['forced_en']='90 days' in answer and '90 dias' not in answer
    return result


def idle(url):
    if not url:return False
    for _ in range(30):
        try:
            slots=httpx.get(url,timeout=5,trust_env=False).json()
            if isinstance(slots,list) and slots and all(s.get('is_processing') is False for s in slots):return True
        except (httpx.HTTPError,ValueError,AttributeError):return False
        time.sleep(1)
    return False


def run(args):
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    if (out/'results.json').exists():raise SystemExit('Choose a new output folder to preserve the earlier attempt.')
    records=[]
    class Recorder(Provider):
        async def complete(self,model,messages,tools):
            row={'model':model,'messages':json.loads(json.dumps(messages))};records.append(row)
            try:
                reply=await super().complete(model,messages,tools);row['response']=reply;return reply
            except Exception as error:
                row['error']=str(error);raise
    app=create_app(ROOT,out/'catalogue.sqlite3',lambda *a:Recorder(*a));data=fixtures(ROOT)
    order=data[2][1];email=data[3][int(order['customer_id'])]['email']
    metadata={'model':args.model,'base_url':args.base_url,'revision':args.revision,'utc':datetime.now(timezone.utc).isoformat(),
        'source_hashes':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'src/emporio').rglob('*.py'))}}
    results=[]
    with ExitStack() as stack:
        clients={}
        for case in cases():
            if args.only and case['id'] not in args.only.split(','):continue
            if case['group'] not in clients:
                client=stack.enter_context(TestClient(app));client.get('/api/bootstrap')
                configured=client.post('/api/config',json={'base_url':args.base_url,'model':args.model,'no_key':True})
                assert configured.status_code==200,configured.text
                clients[case['group']]=client
            client=clients[case['group']];started=time.monotonic();before=len(records)
            if case['kind']=='chat':
                response=client.post('/api/chat',json={'message':case['message'],'language':case['language'],
                    'context':case.get('context_override',case['context'])})
            elif case['kind'].startswith('verify_'):
                response=client.post('/api/orders/verify',json={'order_id':1,'email':email if case['kind']=='verify_correct' else 'wrong@example.invalid'})
            else:response=client.post('/api/chat/reset',json={})
            body=response.json();assertions=checks(case,response.status_code,body,data)
            row={'case':case,'status':response.status_code,'reply':body,'checks':assertions,'passed':all(assertions.values()),
                 'provider_calls':len(records)-before,'seconds':round(time.monotonic()-started,2)}
            results.append(row)
            (out/'results.json').write_text(json.dumps({**metadata,'cases':results},ensure_ascii=False,indent=2),encoding='utf-8')
            (out/'model-requests.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
            print(json.dumps({'case':case['id'],'passed':row['passed'],'seconds':row['seconds'],
                'failed_checks':[k for k,v in assertions.items() if not v],'answer':body.get('answer',body.get('detail','API event'))},ensure_ascii=True),flush=True)
            if response.status_code==502 or body.get('model_error'):
                if not idle(args.slots_url):
                    print('Stopped because the model endpoint could not be confirmed idle.',flush=True);break
    print(f"Passed {sum(r['passed'] for r in results)}/{len(results)} executed steps",flush=True)
    return 0 if results and all(r['passed'] for r in results) else 1


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url',default='http://127.0.0.1:8080/v1')
    parser.add_argument('--model',default='Bonsai27B')
    parser.add_argument('--revision',default='unspecified')
    parser.add_argument('--output',default=str(ROOT/'.runtime/model-acceptance-baseline'))
    parser.add_argument('--only',help='Comma-separated case IDs for an explicitly partial regression run.')
    parser.add_argument('--slots-url',help='Explicit local llama.cpp status URL to confirm idle after timeouts.')
    raise SystemExit(run(parser.parse_args()))

"""Opt-in live comparison conversation and policy regression with recorded model calls."""
import argparse
import asyncio
import json
import time
import httpx
from datetime import datetime, timezone
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from emporio.agent.engine import Agent
from emporio.integrations.provider import Provider
from emporio.session.state import Session
from emporio.web.app import create_app, ROOT

CASES = [
    ('en', 'Compare Yamaha C40 and Yamaha F310. Which is better for me?', [81,87], ['maximum budget', '100.00 less'], ['superior tone']),
    ('en', 'I am a beginner. My budget is R$650 and I prefer nylon strings. I will play at home.', [81,87], ['Yamaha C40 Nylon Natural is the only', 'playing at home'], ['F310 Aço Natural is the only']),
    ('en', 'Actually, I prefer steel strings and my budget is R$800.', [81,87], ['Yamaha F310 Aço Natural is the only'], ['C40 Nylon Natural is the only']),
    ('en', 'I need built-in electronics for amplification.', [81,87], ['None of these instruments'], ['is the only one']),
    ('en', 'Compare Yamaha NTX1 and Takamine GC1CE. My budget is R$3000 and I prefer nylon.', [98,115], ['Takamine GC1CE Elétrico Nylon Natural is the only', 'exceeds your budget'], ['Yamaha NTX1 Elétrico Nylon Natural is the only']),
    ('pt-BR', 'Qual é mais confortável?', [], ['não informa ação', 'experimente'], ['R$', 'soa melhor']),
    ('pt-BR', 'Qual tem o melhor timbre?', [], ['não comprovam o timbre', 'demonstração'], ['R$', 'é superior']),
    ('pt-BR', 'Qual é mais leve?', [], ['peso', 'não está registrado'], ['R$']),
    ('en', 'Can I combine PIX and card above R$2000?', [], ['no 5%', 'promotion'], ['nylon', 'scale length']),
    ('en', 'How long does a refund take?', [], ['10 business days', 'original payment'], ['nylon', 'R$']),
]

async def run(args):
    out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
    app=create_app(ROOT,out/'catalogue.sqlite3');records=[];results=[]
    class Recorder(Provider):
        async def complete(self,model,messages,tools):
            record={'model':model,'messages':json.loads(json.dumps(messages))};records.append(record)
            response=await super().complete(model,messages,tools);record['response']=response;return response
    agent=Agent(app.state.tools,lambda *a:Recorder(*a))
    session=Session(base_url=args.base_url,model=args.model)
    for index,(language,question,ids,required,excluded) in enumerate(CASES):
        session.language=language;start=time.monotonic();before=len(records)
        try:
            reply=await agent.reply(session,question,{})
            checks={'products':[p['product_id'] for p in reply['products']]==ids,
                    'required':all(s in reply['answer'] for s in required),
                    'excluded':not any(s in reply['answer'] for s in excluded),
                    'tool_consulted':any(t['name']==('compare_products' if index<8 else 'lookup_policy') for t in reply['trace'])}
            row={'case':index+1,'language':language,'question':question,'reply':reply,'checks':checks,
                 'passed':all(checks.values()),'provider_calls':len(records)-before,'seconds':round(time.monotonic()-start,2)}
            if reply.get('model_error'):
                row['model_error']=reply['model_error']
        except Exception as error:
            row={'case':index+1,'question':question,'passed':False,'error':str(error)}
        results.append(row)
        (out/'results.json').write_text(json.dumps({'model':args.model,'base_url':args.base_url,'utc':datetime.now(timezone.utc).isoformat(),'cases':results},ensure_ascii=False,indent=2),encoding='utf-8')
        (out/'model-requests.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({k:row[k] for k in ('case','passed','question')},ensure_ascii=True),flush=True)
        if row.get('error'):break
        if row.get('model_error'):
            if not args.slots_url:
                break
            # Timeout need not stop server-side inference. Do not queue another
            # request until the explicitly supplied local status endpoint is idle.
            idle=False
            async with httpx.AsyncClient(trust_env=False,timeout=5) as client:
                for attempt in range(30):
                    try:
                        slots=(await client.get(args.slots_url)).json()
                        idle=isinstance(slots,list) and bool(slots) and all(s.get('is_processing') is False for s in slots)
                    except (httpx.HTTPError,ValueError,AttributeError):
                        break
                    if idle:break
                    await asyncio.sleep(1)
            if not idle:break
    print(f"Passed {sum(r['passed'] for r in results)}/{len(results)} executed cases",flush=True)
    print(f"Model connection failures {sum(bool(r.get('model_error')) for r in results)}",flush=True)
    return 0 if len(results)==len(CASES) and all(r['passed'] and not r.get('model_error') for r in results) else 1

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url',default='http://127.0.0.1:8080/v1')
    parser.add_argument('--model',default='Bonsai27B')
    parser.add_argument('--output',default=str(ROOT/'.runtime/bonsai-advice-evaluation'))
    parser.add_argument('--slots-url',help='Explicit local llama.cpp slots URL, used only to confirm idle after a timeout.')
    raise SystemExit(asyncio.run(run(parser.parse_args())))

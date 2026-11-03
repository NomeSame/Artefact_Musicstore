"""Publish three actual conversations only from a complete, passing acceptance report."""
import argparse
import hashlib
import json
from pathlib import Path
from check_model_acceptance import cases

ROOT=Path(__file__).resolve().parents[1]
GROUPS={
    'catalogue':('01-catalogue-live.md','Catalogue prices, discounts and availability','01_catalogue_preview.md'),
    'orders':('02-orders-live.md','Order verification and session scope','03_order_scope_preview.md'),
    'service':('03-service-context-live.md','Customer service, context and language','02_returns_preview.md'),
}


def publish(source):
    report=json.loads(source.read_text(encoding='utf-8'))
    rows=report['cases'];expected={c['id'] for c in cases()}
    assert len(rows)==len(expected) and {r['case']['id'] for r in rows}==expected,'A complete acceptance run is required.'
    assert all(r['passed'] and all(r['checks'].values()) for r in rows),'Failed cases must not be published as final acceptance.'
    for relative,digest in report['source_hashes'].items():
        assert hashlib.sha256((ROOT/relative.replace('\\','/')).read_bytes()).hexdigest()==digest, f'Application changed after the run: {relative}'
    archive=ROOT/'.runtime/preview-examples-before-acceptance';archive.mkdir(parents=True,exist_ok=True)
    for name in ('01_catalogue_preview.md','02_returns_preview.md','03_order_scope_preview.md'):
        old=ROOT/'examples'/name
        if old.exists():
            backup=archive/name
            if not backup.exists():backup.write_bytes(old.read_bytes())
    for group,(filename,title,_) in GROUPS.items():
        selected=[r for r in rows if r['case']['group']==group]
        parts=[f'# {title}',
            f"This is an actual conversation from the final functional acceptance on 3 November 2026. The configured local model was {report['model']} at `{report['base_url']}`. The server reported Bonsai-27B-Q1_0.gguf with very high reasoning effort. Its settings were not changed. Questions were prepared for evaluation rather than collected from independent customers.",
            'Each group used its own real application session through FastAPI routes and the live model provider. The model selected tools, while the application validated the request evidence and produced the visible factual replies. Direct application clarifications and API verification events are identified separately. This evaluates the application with the model and does not attribute every correct sentence to free model generation.',
            f"This conversation contains {sum(r['case']['kind']=='chat' for r in selected)} chat turns and {sum(r['case']['kind']!='chat' for r in selected)} API events. It made {sum(r['provider_calls'] for r in selected)} provider calls. All its recorded checks passed. The complete run passed {len(rows)} steps across three sessions, including independently calculated CSV price expectations.",
            f"The report revision label is `{report['revision']}`. It describes a working tree based on the stated commit, not a new commit ID. The exact application hashes, actual replies, checks and model requests are recorded under `{source.parent.relative_to(ROOT).as_posix()}`. Earlier failed attempts remain in separate runtime folders. The reproducible runner is `scripts/check_model_acceptance.py`. This was functional acceptance, and the separate final injection campaign is still open."]
        for row in selected:
            case=row['case'];parts.append(f"## {case['id']}")
            if case['kind']=='chat':
                context=case.get('context_override',case['context'])
                details=[]
                if context.get('selected_product_id'):details.append(f"selected product {context['selected_product_id']}")
                if context.get('category_id'):details.append(f"category {context['category_id']}")
                if context.get('visible_product_ids'):details.append('visible products '+', '.join(map(str,context['visible_product_ids'])))
                details.append('payment setting '+context.get('payment','unspecified'))
                parts += [f"The site language was {case['language']}, with "+', '.join(details)+f". This turn made {row['provider_calls']} provider calls and took {row['seconds']} seconds.",
                          '**Customer**',case['message'],'**Empório Guide**',row['reply']['answer']]
                if row['reply'].get('products'):
                    cards=['The interface displayed these product cards.']
                    cards += [f"- {p['name']}, R$ {p['price_cents']/100:,.2f}, "+('available.' if p['available'] else 'unavailable.') for p in row['reply']['products']]
                    parts.append(cards[0]+'\n\n'+'\n'.join(cards[1:]))
                tools=list(dict.fromkeys(t['name'] for t in row['reply'].get('trace',[])))
                if tools:
                    parts.append('Recorded tools were '+', '.join(f'`{t}`' for t in tools)+'.')
                elif row['provider_calls']:
                    parts.append('The model made no tool call. The application used its controlled greeting or shop-scope reply.')
                else:
                    parts.append('No tool or provider call was needed for this application clarification.')
            else:
                events={
                    'verify_wrong':'The evaluator submitted order 1 with a deliberately non-matching email through the order lookup route. It returned HTTP 403 and did not verify the session.',
                    'verify_correct':'The evaluator submitted order 1 with the matching email from the supplied fictional customer data through the order lookup route. It returned HTTP 200 and verified that order in this session. The email is omitted here.',
                    'reset':'The evaluator reset this conversation through the application route. It returned HTTP 200. The next chat request tests the cleared verification state.',
                }
                parts.append(events[case['kind']])
        (ROOT/'examples'/filename).write_bytes(('\n\n'.join(parts)+'\n').encode('utf-8'))
    for name in ('01_catalogue_preview.md','02_returns_preview.md','03_order_scope_preview.md'):
        old=ROOT/'examples'/name
        if old.exists():
            assert (archive/name).exists()
            old.unlink()
    print('Published three actual acceptance conversations, preserved the original previews locally and retained five public conversation files.')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report',type=Path)
    publish(parser.parse_args().report.resolve())

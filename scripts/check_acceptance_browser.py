"""Opt-in real browser/model check for a PIX quote, order verification and language."""
import argparse
import csv
import json
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]

def main(args):
    def rows(name):
        return list(csv.DictReader((ROOT/'data'/f'desafio_tecnico_ai_eng - {name}.csv').open(encoding='utf-8-sig')))
    order=next(o for o in rows('orders') if o['order_id']=='1')
    customer=next(c for c in rows('customers') if c['customer_id']==order['customer_id'])
    report={'model':args.model,'api_base':args.api_base,'steps':[]}
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,channel='msedge')
        page=browser.new_page(viewport={'width':1600,'height':1050})
        errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(args.url,wait_until='networkidle')
        page.locator('#open-settings').click()
        page.locator('#base-url').fill(args.api_base)
        page.locator('#model-id').fill(args.model)
        page.locator('#no-key').check()
        page.locator('#settings-form button[type="submit"]').click()
        expect(page.locator('#settings-dialog')).not_to_be_visible()
        expect(page.locator('#mode-label')).to_contain_text(args.model)
        def send(message):
            page.locator('#chat-input').fill(message)
            with page.expect_response(lambda r:r.request.method=='POST' and r.url.endswith('/api/chat'),timeout=125000) as event:
                page.locator('#send-button').click()
            response=event.value;body=response.json()
            report['steps'].append({'message':message,'status':response.status,'reply':body})
            assert response.status==200,body
            expect(page.locator('#send-button')).to_be_enabled()
            return page.locator('.assistant-message').last,body
        page.locator('[data-category="5"]').click()
        page.locator('.product-art[data-product="81"]').click()
        page.locator('#ask-product').click()
        answer,body=send('What does this instrument cost with full immediate PIX payment?')
        expect(answer).to_contain_text('569.91')
        assert body['products'][0]['product_id']==81 and body['products'][0]['price_cents']==56991
        page.locator('#order-lookup').click()
        page.locator('#order-id').fill('1')
        page.locator('#order-email').fill('wrong@example.invalid')
        page.locator('#order-form button[type="submit"]').click()
        expect(page.locator('#order-result')).to_contain_text('do not match')
        page.locator('#order-email').fill(customer['email'])
        page.locator('#order-form button[type="submit"]').click()
        expect(page.locator('#order-result')).to_contain_text(order['tracking_code'])
        expect(page.locator('#order-email')).to_have_value('')
        page.locator('#order-dialog .close-dialog').click()
        answer,body=send('What is the status and tracking reference of order 1?')
        expect(answer).to_contain_text(order['status'])
        expect(answer).to_contain_text(order['tracking_code'])
        page.locator('[data-language="pt-BR"]').click()
        expect(page.locator('#send-button')).to_be_enabled()
        answer,body=send('What warranty term is recorded for this instrument? Please answer in English.')
        expect(answer).to_contain_text('90 dias')
        assert body['language']=='pt-BR'
        expect(answer.locator('p').first).to_be_in_viewport()
        page.locator('.assistant-panel').screenshot(path=str(ROOT/'.runtime/acceptance-live-desktop.png'))
        page.set_viewport_size({'width':390,'height':844})
        page.locator('.assistant-panel').scroll_into_view_if_needed()
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        page.locator('.assistant-panel').screenshot(path=str(ROOT/'.runtime/acceptance-live-mobile.png'))
        assert not errors,errors
        (ROOT/'.runtime/acceptance-browser.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        browser.close()
    print('Live-model browser acceptance passed: configured model, selected-product PIX price, wrong and correct order email, verified chat lookup, forced PT-BR and mobile layout.')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url',default='http://127.0.0.1:8770')
    parser.add_argument('--api-base',required=True)
    parser.add_argument('--model',required=True)
    main(parser.parse_args())

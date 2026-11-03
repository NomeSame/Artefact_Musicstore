"""Real UI acceptance for comparison cards, preferences, locale and reset."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]
BASE=os.environ.get('EMPORIO_TEST_URL','http://127.0.0.1:8770')

def main():
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,channel='msedge')
        page=browser.new_page(viewport={'width':1600,'height':1050})
        errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(BASE,wait_until='networkidle')
        def send(message):
            page.locator('#chat-input').fill(message)
            page.locator('#send-button').click()
            expect(page.locator('#send-button')).to_be_enabled()
            return page.locator('.assistant-message').last
        answer=send('Compare C40 and F310. Which is better for me?')
        expect(answer).to_contain_text('maximum budget')
        expect(answer.locator('.chat-product')).to_have_count(2)
        answer=send('My budget is R$650 and I prefer nylon strings.')
        expect(answer).to_contain_text('C40 Nylon Natural is the only')
        page.locator('[data-language="pt-BR"]').click()
        expect(page.locator('#send-button')).to_be_enabled()
        answer=send('Meu orçamento é R$800 e prefiro cordas de aço.')
        expect(answer).to_contain_text('F310 Aço Natural é o único')
        answer.locator('.chat-product').first.click()
        expect(page.locator('#product-dialog')).to_be_visible()
        page.locator('#product-dialog .close-dialog').click()
        answer=send('Qual é mais confortável?')
        expect(answer).to_contain_text('não informa ação')
        expect(answer).not_to_contain_text('R$')
        expect(answer.locator('p').first).to_be_in_viewport()
        page.locator('.assistant-panel').screenshot(path=str(ROOT/'.runtime/advice-chat-desktop.png'))
        page.set_viewport_size({'width':390,'height':844})
        answer=send('Qual tem o melhor timbre?')
        expect(answer).to_contain_text('não comprovam o timbre')
        expect(answer.locator('p').first).to_be_in_viewport()
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        page.locator('.assistant-panel').screenshot(path=str(ROOT/'.runtime/advice-chat-mobile.png'))
        page.locator('#chat-menu').click()
        page.locator('#reset-chat').click()
        answer=send('Qual é melhor para mim?')
        expect(answer).to_contain_text('Quais dois ou três modelos')
        assert not errors,errors
        browser.close()
    print('Advice browser checks passed: comparison cards, revised preferences, language change, detail link, narrow follow-up, mobile layout and reset.')

if __name__=='__main__':main()

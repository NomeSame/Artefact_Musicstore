"""Product-page and deliberate chat handoff acceptance checks."""
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]
BASE=os.environ.get("EMPORIO_TEST_URL","http://127.0.0.1:8770")
def main():
    errors=[]
    requests=[]
    with sync_playwright() as playwright:
        browser=playwright.chromium.launch(headless=True,channel="msedge")
        page=browser.new_page(viewport={"width":1600,"height":1050},device_scale_factor=1)
        page.on("pageerror",lambda error:errors.append(str(error)))
        page.on("request",lambda request:requests.append(request.post_data_json)
                if request.method=="POST" and request.url.endswith("/api/chat") else None)
        page.goto(BASE,wait_until="networkidle")
        page.locator('[data-category="5"]').click()
        expect(page.locator("#catalogue-title")).to_have_text("Acoustic guitars")
        page.locator('.product-art[data-product="81"]').click()
        expect(page.locator("#product-dialog")).to_be_visible()
        page.locator("#ask-product").click()
        expect(page.locator("#product-dialog")).not_to_be_visible()
        expect(page.locator("#chat-input")).to_be_focused()
        expect(page.locator("#chat-input")).to_have_value("")
        expect(page.locator("#product-questions")).to_be_visible()
        assert len(requests)==0
        page.locator('#product-questions [data-topic="0"]').click()
        expect(page.locator("#chat-input")).to_have_value(
            "What are the materials and technical specifications of this instrument?")
        assert len(requests)==0
        page.locator("#send-button").click()
        expect(page.locator("#messages")).to_contain_text("Spruce")
        expect(page.locator("#messages")).to_contain_text("650mm")
        assert len(requests)==1
        assert requests[0]["context"]["selected_product_id"]==81
        page.locator('.product-art[data-product="81"]').click()
        page.locator("#view-product-page").click()
        expect(page).to_have_url(BASE+"/products/81")
        expect(page.locator("#product-page h1")).to_have_text("Yamaha C40 Nylon Natural")
        expect(page.locator("#product-specs")).to_contain_text("Spruce")
        expect(page.locator("#product-store-policies")).to_contain_text("Warranty")
        expect(page.locator("#product-buying")).to_contain_text("not recorded")
        assert len(requests)==1
        page.screenshot(path=str(ROOT/".runtime/product-page-desktop.png"))
        page.locator('#product-page [data-question="1"]').click()
        expect(page.locator("#chat-input")).to_be_focused()
        expect(page.locator("#chat-input")).to_have_value(
            "What sound-related specifications and electronics are recorded for this instrument?")
        assert len(requests)==1
        page.locator("#send-button").click()
        expect(page.locator("#messages")).to_contain_text("Electronics: no")
        assert len(requests)==2
        page.locator("#page-own-question").click()
        expect(page.locator("#chat-input")).to_have_value("")
        expect(page.locator("#chat-input")).to_be_focused()
        assert len(requests)==2
        page.go_back()
        expect(page.locator("#catalogue-view")).to_be_visible()
        expect(page.locator("#messages")).to_contain_text("Spruce")
        page.go_forward()
        expect(page.locator("#product-page h1")).to_have_text("Yamaha C40 Nylon Natural")
        page.reload(wait_until="networkidle")
        expect(page.locator("#product-page h1")).to_have_text("Yamaha C40 Nylon Natural")
        page.set_viewport_size({"width":390,"height":844})
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        page.screenshot(path=str(ROOT/".runtime/product-page-mobile.png"))
        page.locator("#page-own-question").click()
        expect(page.locator("#chat-input")).to_be_focused()
        expect(page.locator("#chat-input")).to_have_value("")
        expect(page.locator("#chat-input")).to_be_in_viewport(timeout=5000)
        assert len(requests)==2
        page.locator("#page-ask-product").click()
        expect(page.locator("#product-questions")).to_be_visible()
        assert len(requests)==2
        page.locator(".assistant-panel").screenshot(path=str(ROOT/".runtime/product-page-chat.png"))
        assert not errors,errors
        browser.close()
    print("Product flow passed: direct URL, reload, history, details, deliberate drafts, zero auto-send, free question, selected context and mobile focus.")
if __name__=="__main__":
    main()

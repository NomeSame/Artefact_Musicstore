"""Optional local browser acceptance checks using an installed Chromium browser."""
from pathlib import Path
import os
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]
def main():
    errors=[]
    with sync_playwright() as playwright:
        candidates=[
            Path("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"),
            Path("C:/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe"),
            Path("/usr/bin/chromium"),Path("/usr/bin/google-chrome"),
        ]
        executable=next((str(p) for p in candidates if p.exists()),None)
        browser=playwright.chromium.launch(headless=True,**({"executable_path":executable} if executable else {}))
        page=browser.new_page(viewport={"width":1600,"height":1050},device_scale_factor=1)
        page.on("pageerror",lambda error:errors.append(str(error)))
        page.goto(os.environ.get("EMPORIO_TEST_URL","http://127.0.0.1:8765"),wait_until="networkidle")
        expect(page.locator(".product-card")).to_have_count(65)
        expect(page.locator("#result-count")).to_have_text("65 instruments")
        output=ROOT/".runtime"
        output.mkdir(exist_ok=True)
        page.screenshot(path=str(output/"preview-desktop.png"))
        page.locator('[data-category="5"]').click()
        page.locator("#toggle-filters").click()
        page.locator("#max-price").fill("1000")
        page.locator("#max-price").dispatch_event("change")
        expect(page.locator("#catalogue-title")).to_have_text("Acoustic guitars")
        page.wait_for_timeout(300)
        assert page.locator(".product-card").count()>0
        page.locator(".product-art").first.click()
        expect(page.locator("#product-dialog")).to_be_visible()
        page.locator("#ask-product").click()
        expect(page.locator("#chat-input")).to_have_value("")
        expect(page.locator("#product-questions")).to_be_visible()
        page.locator('#product-questions [data-topic="0"]').click()
        expect(page.locator("#chat-input")).to_have_value("What are the materials and technical specifications of this instrument?")
        page.locator("#send-button").click()
        expect(page.locator("#messages")).to_contain_text("recorded specifications")
        expect(page.locator("#messages")).to_contain_text("get_product")
        page.locator("#open-settings").click()
        expect(page.locator("#settings-dialog")).to_be_visible()
        page.locator("#provider-preset").select_option("http://localhost:1234/v1")
        expect(page.locator("#base-url")).to_have_value("http://localhost:1234/v1")
        expect(page.locator("#no-key")).to_be_checked()
        page.locator("#use-preview").click()
        page.locator("#chat-menu").click()
        page.locator("#open-tools").click()
        expect(page.locator("#tool-list")).to_contain_text("search_products")
        page.locator("#tools-dialog .close-dialog").click()
        page.locator("#search").fill("no-such-instrument-xyz")
        expect(page.locator("#empty")).to_be_visible()
        page.locator("#clear-search").click()
        expect(page.locator(".product-card")).to_have_count(65)
        page.set_viewport_size({"width":390,"height":844})
        expect(page.locator(".product-card")).to_have_count(65)
        page.screenshot(path=str(output/"preview-mobile.png"))
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        page.locator("#order-lookup").click()
        expect(page.locator("#order-dialog")).to_be_visible()
        page.locator("#order-id").fill("1")
        page.locator("#order-email").fill("wrong@example.test")
        page.locator('#order-form button[type="submit"]').click()
        expect(page.locator("#order-result")).to_contain_text("do not match")
        page.locator("#order-dialog .close-dialog").click()
        page.locator("#chat-input").fill("What are the return rules?")
        page.locator("#send-button").click()
        expect(page.locator("#messages")).to_contain_text("actual receipt date")
        page.locator(".assistant-panel").screenshot(path=str(output/"preview-chat.png"))
        assert not errors,errors
        browser.close()
    print("Browser checks passed: catalogue, filters, product context, preview chat, settings, tools, order failure, mobile layout.")
if __name__=="__main__":
    main()

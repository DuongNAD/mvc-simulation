import os
import pytest
from playwright.sync_api import sync_playwright, Page, expect

INDEX_HTML_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../index.html")).replace("\\", "/")
INDEX_URL = f"file:///{INDEX_HTML_PATH}"

@pytest.fixture(scope="function")
def page():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        yield page
        browser.close()

def test_adversarial_special_replacements_match(page: Page):
    """Verify how the R6 panel handles special JavaScript replace substitution string '$&'."""
    page.goto(INDEX_URL)
    
    special_name = "Alice $& Bob"
    page.fill("#studentName", special_name)
    page.click("#startBtn")
    
    expect(page.locator("#r6-active-file")).to_have_text("Main.java")
    
    input_text = page.locator("#r6-class-input").inner_text()
    output_text = page.locator("#r6-class-output").inner_text()
    
    # Assert that the name in the panel is actually 'Alice $& Bob' and NOT containing 'Nguyễn Văn A'
    assert "Nguyễn Văn A" not in input_text, "R6 panel leaked 'Nguyễn Văn A' due to $& substitution!"
    assert "Alice $& Bob" in input_text, "R6 panel failed to render 'Alice $& Bob' correctly!"

def test_adversarial_special_replacements_preceding(page: Page):
    """Verify how the R6 panel handles special JavaScript replace substitution string '$`'."""
    page.goto(INDEX_URL)
    
    special_name = "Alice $` Bob"
    page.fill("#studentName", special_name)
    page.click("#startBtn")
    
    expect(page.locator("#r6-active-file")).to_have_text("Main.java")
    
    input_text = page.locator("#r6-class-input").inner_text()
    
    assert "Nguyễn Văn A" not in input_text, "R6 panel leaked 'Nguyễn Văn A' due to $` substitution!"
    assert "Alice $` Bob" in input_text, "R6 panel failed to render 'Alice $` Bob' correctly!"

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

def test_backward_stepping_db_id(page: Page):
    """Verify database ID rendering consistency when stepping backward and forward."""
    page.goto(INDEX_URL)
    
    page.fill("#studentName", "Bob")
    page.click("#startBtn") # Step 1: Main (currentStep = 1)
    
    # Step forward to Step 6 (Repo/Service/Controller)
    for _ in range(5):
        page.click("#nextBtn")
        
    expect(page.locator("#current-step-num")).to_have_text("6")
    expect(page.locator("#r6-active-file")).to_have_text("StudentResponseDTO.java")
    
    # Assert id is 1
    input_text_6 = page.locator("#r6-class-input").inner_text()
    output_text_6 = page.locator("#r6-class-output").inner_text()
    assert "id: 1" in input_text_6, f"Expected 'id: 1' in Step 6 input, got: {input_text_6}"
    
    # Step backward to Step 5 (Model)
    page.click("#prevBtn")
    expect(page.locator("#current-step-num")).to_have_text("5")
    expect(page.locator("#r6-active-file")).to_have_text("Student.java")
    
    # Assert id is 1 at Step 5 backward
    input_text_5 = page.locator("#r6-class-input").inner_text()
    output_text_5 = page.locator("#r6-class-output").inner_text()
    print(f"\nStep 5 input during backward step: {input_text_5}")
    print(f"Step 5 output during backward step: {output_text_5}")
    
    assert "id: 1" in input_text_5, f"Expected 'id: 1' in Step 5 input, got: {input_text_5}"
    assert "id: 1" in output_text_5, f"Expected 'id: 1' in Step 5 output, got: {output_text_5}"

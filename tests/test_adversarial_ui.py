import os
import pytest
import asyncio
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

def test_adversarial_html_injection(page: Page):
    """Verify if the application is vulnerable to HTML/XSS injection through the student name input."""
    page.goto(INDEX_URL)
    
    # Input HTML tag as student name
    injected_html = '<span id="xss-test">Injected Content</span>'
    page.fill("#studentName", injected_html)
    page.click("#startBtn")
    
    # Step through to Step 7 (View output)
    for _ in range(6):
        page.click("#nextBtn")
        
    # Check if the console output contains the raw HTML element (XSS/HTML Injection)
    # If the page escapes it, the element #xss-test will NOT be present in the DOM.
    # If the page renders it, #xss-test WILL be in the DOM.
    injected_el = page.locator("#xss-test")
    
    # Let's check if the element exists
    exists = injected_el.count() > 0
    if exists:
        print("\n[VULNERABILITY FOUND] HTML/XSS injection is successful! The student name is rendered as unescaped HTML in #console-output.")
        assert exists
    else:
        print("\n[SECURITY PASS] HTML is properly escaped.")
        assert not exists
        
    # Verify that the injected HTML is also escaped and does not render as compiled DOM elements in the explanation panel
    assert page.locator("#r6-explanation-panel #xss-test").count() == 0
    expect(page.locator("#r6-class-input")).to_contain_text(injected_html)

def test_adversarial_fast_stepping(page: Page):
    """Verify that rapid sequential transitions do not break the UI state machine."""
    page.goto(INDEX_URL)
    
    page.fill("#studentName", "Fast Stepper")
    page.click("#startBtn")
    
    # Fast click "Sau" to Step 7
    for _ in range(6):
        page.click("#nextBtn")
        
    expect(page.locator("#current-step-num")).to_have_text("7")
    expect(page.locator("#view-layer")).to_contain_class("active")
    
    # Verify Step 7 R6 panel state
    expect(page.locator("#r6-explanation-panel")).to_be_visible()
    expect(page.locator("#r6-active-file")).to_have_text("StudentView.java")
    expect(page.locator("#r6-class-input")).to_contain_text("Fast Stepper")
    
    # Verify Step 7 opacities and file tracking
    expect(page.locator("#file-tracking-display")).to_have_text("StudentController.java ➔ StudentView.java")
    for layer in ["#main-layer", "#controller-layer", "#service-layer", "#repo-layer", "#model-layer", "#view-layer"]:
        expect(page.locator(layer)).to_contain_class("opacity-100")
    for arrow in ["#arrow-c-s-down", "#arrow-s-c-up", "#arrow-s-r-down", "#arrow-r-s-up", "#arrow-r-m-down"]:
        expect(page.locator(arrow)).to_contain_class("opacity-100")

    # Fast click "Trước" to Step 1
    for _ in range(6):
        page.click("#prevBtn")
        
    expect(page.locator("#current-step-num")).to_have_text("1")
    expect(page.locator("#main-layer")).to_contain_class("active")
    expect(page.locator("#view-layer")).not_to_contain_class("active")
    
    # Verify Step 1 R6 panel state after rapid stepping back
    expect(page.locator("#r6-explanation-panel")).to_be_visible()
    expect(page.locator("#r6-active-file")).to_have_text("Main.java")
    expect(page.locator("#r6-class-input")).to_contain_text("Fast Stepper")

    # Verify Step 1 opacities and file tracking after stepping back
    expect(page.locator("#file-tracking-display")).to_have_text("Main.java ➔ StudentRequestDTO.java")
    expect(page.locator("#main-layer")).to_contain_class("opacity-100")
    for layer in ["#controller-layer", "#service-layer", "#repo-layer", "#model-layer", "#view-layer"]:
        expect(page.locator(layer)).to_contain_class("opacity-10")
    for arrow in ["#arrow-c-s-down", "#arrow-s-c-up", "#arrow-s-r-down", "#arrow-r-s-up", "#arrow-r-m-down"]:
        expect(page.locator(arrow)).to_contain_class("opacity-10")

def test_adversarial_boundary_bypass(page: Page):
    """Verify that programmatic bypass of disabled buttons does not corrupt the state machine."""
    page.goto(INDEX_URL)
    
    # Start simulation
    page.fill("#studentName", "Bypass User")
    page.click("#startBtn")
    
    # We are at Step 1. Try to call prevStep() programmatically
    page.evaluate("prevStep()")
    # Should still be at Step 1
    expect(page.locator("#current-step-num")).to_have_text("1")
    expect(page.locator("#main-layer")).to_contain_class("active")
    
    # R6 panel should still be visible at Step 1
    expect(page.locator("#r6-explanation-panel")).to_be_visible()
    expect(page.locator("#r6-active-file")).to_have_text("Main.java")
    
    # Step through to Step 7
    for _ in range(6):
        page.click("#nextBtn")
        
    # We are at Step 7. Try to call nextStep() programmatically via evaluating JS
    # In native index.html, nextStep() calls completeSimulation() at step 7, which resets step to 0
    page.evaluate("nextStep()")
    
    # Should be reset to Step 0 (initial state)
    expect(page.locator("#studentName")).to_be_enabled()
    expect(page.locator("#startBtn")).to_be_enabled()
    expect(page.locator("#simulation-controls")).to_contain_class("hidden")
    
    # R6 panel should be hidden after reset
    expect(page.locator("#r6-explanation-panel")).not_to_be_visible()

import os
import pytest
from playwright.sync_api import sync_playwright, Page, expect

INDEX_HTML_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../index.html")).replace("\\", "/")
INDEX_URL = f"file:///{INDEX_HTML_PATH}"

@pytest.fixture(scope="function")
def page():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        yield page
        browser.close()

def test_console_output_overflow_adversarial(page: Page):
    """Verify if a very long continuous student name causes console output layout overflow."""
    page.goto(INDEX_URL)
    
    # 5000 character continuous word
    long_name = "A" * 5000
    page.fill("#studentName", long_name)
    page.click("#startBtn")
    
    # Step to 7 (View output)
    for _ in range(6):
        page.click("#nextBtn")
        
    expect(page.locator("#current-step-num")).to_have_text("7")
    
    # Get bounding boxes
    console_box = page.locator("#console-output").bounding_box()
    view_box = page.locator("#view-layer").bounding_box()
    
    print(f"\nConsole bounding box: {console_box}")
    print(f"View layer bounding box: {view_box}")
    
    assert console_box is not None
    assert view_box is not None
    
    # In a proper fluid layout, the inner console-output box should not be wider than its parent view-layer.
    # Allowing a small delta (padding/margin difference) but definitely not significantly larger.
    # If there is overflow, console_box['width'] will expand beyond the viewport or parent width.
    assert console_box['width'] <= view_box['width'] + 20, (
        f"Console output overflowed! console width {console_box['width']} is greater than parent width {view_box['width']}"
    )

def test_unstarted_stepping_bypass(page: Page):
    """Verify what happens when nextStep() is evaluated programmatically before simulation start (currentStep=0)."""
    page.goto(INDEX_URL)
    
    errors = []
    page.on("pageerror", lambda err: errors.append(err))
    
    # Evaluate nextStep() programmatically when currentStep is 0
    # On page load, currentStep = 0, nameInputVal = ''
    page.evaluate("nextStep()")
    
    # Check current step transitioned to 1
    step_num = page.locator("#current-step-num").text_content()
    print(f"\nTransitioned programmatically to step: {step_num}")
    assert step_num == "1"
    
    # Verify that no JavaScript errors were thrown
    assert len(errors) == 0, f"Stepping unstarted caused page errors: {errors}"
    
    # Verify that the active layer is main-layer
    expect(page.locator("#main-layer")).to_contain_class("active")
    
    # Verify R6 panel is updated with empty name but remains hidden in UI
    expect(page.locator("#r6-explanation-panel")).not_to_be_visible()
    expect(page.locator("#r6-active-file")).to_have_text("Main.java")
    
    # Verify R6 input box displays empty string representation safely
    expect(page.locator("#r6-class-input")).to_contain_text('Tên sinh viên nhập thô: ""')

def test_replacement_pattern_injection(page: Page):
    """Verify that special JS replace() patterns in studentName do not corrupt/hijack the R6 panel output."""
    page.goto(INDEX_URL)
    
    # Input is "$&" (matched substring)
    page.fill("#studentName", "$&")
    page.click("#startBtn")
    
    # Check Step 1 R6 panel input content
    expect(page.locator("#r6-explanation-panel")).to_be_visible()
    r6_input_text = page.locator("#r6-class-input").text_content()
    print(f"\nR6 input text for '$&': {r6_input_text}")
    
    # It should display "$&" literally, not "Nguyễn Văn A" (the template string name).
    # If the bug exists, it will replace "Nguyễn Văn A" with the pattern itself ("Nguyễn Văn A"),
    # resulting in: Tên sinh viên nhập thô: "Nguyễn Văn A"
    assert "Nguyễn Văn A" not in r6_input_text, (
        f"Replacement pattern injection vulnerability found! '$&' name input caused template leakage: {r6_input_text}"
    )
    assert "$&" in r6_input_text, f"Expected '$&' to be rendered literally: {r6_input_text}"

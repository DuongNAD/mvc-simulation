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

def test_stress_validation_bounds(page: Page):
    """Verify that extreme inputs, unicode, SQL injection, and script elements are safely handled without layout breakage or execution errors."""
    page.goto(INDEX_URL)
    
    # 1. Very long name (1000 characters)
    long_name = "A" * 1000
    page.fill("#studentName", long_name)
    page.click("#startBtn")
    
    # Check that simulation starts successfully
    expect(page.locator("#r6-explanation-panel")).to_be_visible()
    expect(page.locator("#r6-active-file")).to_have_text("Main.java")
    input_text = page.locator("#r6-class-input").inner_text()
    assert len(input_text) > 1000
    
    # Run to completion
    for _ in range(7):
        page.click("#nextBtn")
    expect(page.locator("#r6-explanation-panel")).not_to_be_visible()
    
    # 2. Unicode and accented characters
    unicode_name = "𝓣𝓮𝓼𝓽 𝓝𝓪𝓶𝓮 🌟 🚀 12345 Nguyễn Văn A"
    page.fill("#studentName", unicode_name)
    page.click("#startBtn")
    expect(page.locator("#r6-explanation-panel")).to_be_visible()
    expect(page.locator("#r6-class-input")).to_contain_text(unicode_name)
    
    # Complete run
    for _ in range(7):
        page.click("#nextBtn")
        
    # 3. SQL Injection pattern
    sql_name = "'; DROP TABLE students; --"
    page.fill("#studentName", sql_name)
    page.click("#startBtn")
    expect(page.locator("#r6-explanation-panel")).to_be_visible()
    
    # Since single quotes are NOT escaped in updateR6Panel now, we expect the raw form
    expect(page.locator("#r6-class-input")).to_contain_text(sql_name)
    for _ in range(7):
        page.click("#nextBtn")

def test_stress_replacement_patterns(page: Page):
    """Verify that JavaScript special replacement patterns like $&, $`, $', $$, $1, $2 do not break or leak data in the R6 panel."""
    patterns = ["$&", "$`", "$'", "$$", "$1", "$2", "$99", "$&_test_$`_$'"]
    
    for pat in patterns:
        page.goto(INDEX_URL)
        page.fill("#studentName", pat)
        page.click("#startBtn")
        
        # Verify Main.java R6 step 1 renders exactly the input pattern without leaking template defaults
        expect(page.locator("#r6-active-file")).to_have_text("Main.java")
        input_text = page.locator("#r6-class-input").inner_text()
        output_text = page.locator("#r6-class-output").inner_text()
        
        assert "Nguyễn Văn A" not in input_text, f"Replacement pattern {pat} leaked Nguyễn Văn A in input!"
        assert "Nguyễn Văn A" not in output_text, f"Replacement pattern {pat} leaked Nguyễn Văn A in output!"
        
        # Since single quotes are NOT escaped in updateR6Panel now, we expect the raw form
        assert pat in input_text, f"Replacement pattern {pat} not rendered in input!"
        assert pat in output_text, f"Replacement pattern {pat} not rendered in output!"
        
        # Step through to Step 5 (Model.java)
        for _ in range(4):
            page.click("#nextBtn")
            
        expect(page.locator("#r6-active-file")).to_have_text("Student.java")
        model_input = page.locator("#r6-class-input").inner_text()
        model_output = page.locator("#r6-class-output").inner_text()
        assert "Nguyễn Văn A" not in model_input
        assert "Nguyễn Văn A" not in model_output
        assert pat in model_input
        assert pat in model_output
        
        # Reset/Complete
        for _ in range(3):
            page.click("#nextBtn")
        expect(page.locator("#r6-explanation-panel")).not_to_be_visible()

def test_stress_stepping_behavior(page: Page):
    """Verify stepping backward and forward, database popping, and state resets under rapid changes."""
    page.goto(INDEX_URL)
    page.fill("#studentName", "Stepping Tester")
    page.click("#startBtn")
    
    # Trace 1 -> 2 -> 3 -> 2 -> 3 -> 4 -> 5
    expect(page.locator("#current-step-num")).to_have_text("1")
    page.click("#nextBtn")  # 2
    expect(page.locator("#current-step-num")).to_have_text("2")
    page.click("#nextBtn")  # 3
    expect(page.locator("#current-step-num")).to_have_text("3")
    page.click("#prevBtn")  # 2
    expect(page.locator("#current-step-num")).to_have_text("2")
    expect(page.locator("#r6-active-file")).to_have_text("StudentController.java")
    
    page.click("#nextBtn")  # 3
    page.click("#nextBtn")  # 4
    page.click("#nextBtn")  # 5 (Model layer inserts database)
    expect(page.locator("#current-step-num")).to_have_text("5")
    expect(page.locator("#r6-active-file")).to_have_text("Student.java")
    
    # Check database has record
    db_text = page.locator("#database-content").inner_text()
    assert "Stepping Tester" in db_text
    
    # Step backward to 4 (Repository - prepare CREATE)
    page.click("#prevBtn")
    expect(page.locator("#current-step-num")).to_have_text("4")
    expect(page.locator("#r6-active-file")).to_have_text("StudentRepository.java")
    
    # Verify database rolled back/popped
    db_text_rolled = page.locator("#database-content").inner_text()
    assert "Stepping Tester" not in db_text_rolled
    assert "Database trống" in db_text_rolled
    
    # Step forward again to 5
    page.click("#nextBtn")
    expect(page.locator("#current-step-num")).to_have_text("5")
    db_text_readded = page.locator("#database-content").inner_text()
    assert "Stepping Tester" in db_text_readded
    
    # Step all the way to 7
    page.click("#nextBtn")  # 6
    page.click("#nextBtn")  # 7
    expect(page.locator("#current-step-num")).to_have_text("7")
    
    # Complete
    page.click("#nextBtn")
    expect(page.locator("#r6-explanation-panel")).not_to_be_visible()

def test_stress_dynamic_rendering_and_accumulation(page: Page):
    """Verify that multiple runs accumulate database entries correctly and that database IDs and current dates are rendered dynamically in the R6 panel."""
    page.goto(INDEX_URL)
    
    # Get local current date in YYYY-MM-DD format as generated by client JS
    current_date = page.evaluate("() => new Date().toISOString().split('T')[0]")
    
    # Run 1: First Student
    page.fill("#studentName", "First Student")
    page.click("#startBtn")
    
    # Step to 5 (Model)
    for _ in range(4):
        page.click("#nextBtn")
    expect(page.locator("#r6-active-file")).to_have_text("Student.java")
    
    # Assert ID is 1 in inputs/outputs
    expect(page.locator("#r6-class-input")).to_contain_text("id: 1")
    expect(page.locator("#r6-class-input")).to_contain_text(current_date)
    expect(page.locator("#r6-class-output")).to_contain_text("id: 1")
    expect(page.locator("#r6-class-output")).to_contain_text(current_date)
    
    # Complete Run 1
    for _ in range(3):
        page.click("#nextBtn")
        
    # Run 2: Second Student
    page.fill("#studentName", "Second Student")
    page.click("#startBtn")
    
    # Step 1 opacity check: main is active/opacity-100, but view-layer is opacity-10 in step 1 (only becomes opacity-100 in step 7)
    expect(page.locator("#main-layer")).to_contain_class("opacity-100")
    expect(page.locator("#view-layer")).to_contain_class("opacity-10")
    expect(page.locator("#controller-layer")).to_contain_class("opacity-10")
    
    # Step to 5 (Model)
    for _ in range(4):
        page.click("#nextBtn")
    expect(page.locator("#r6-active-file")).to_have_text("Student.java")
    
    # Assert ID is 2 in inputs/outputs (db size is 1 from run 1, so new entity is 2)
    expect(page.locator("#r6-class-input")).to_contain_text("id: 2")
    expect(page.locator("#r6-class-input")).to_contain_text(current_date)
    expect(page.locator("#r6-class-output")).to_contain_text("id: 2")
    expect(page.locator("#r6-class-output")).to_contain_text(current_date)
    
    # Check that layer opacities updated dynamically (Step 5: main, controller, service, repo, model should be active)
    expect(page.locator("#controller-layer")).to_contain_class("opacity-100")
    expect(page.locator("#service-layer")).to_contain_class("opacity-100")
    expect(page.locator("#repo-layer")).to_contain_class("opacity-100")
    expect(page.locator("#model-layer")).to_contain_class("opacity-100")
    expect(page.locator("#view-layer")).to_contain_class("opacity-10")
    
    # Step back to 4, check opacity of model-layer and arrow-r-m-down reverts to opacity-10
    page.click("#prevBtn")
    expect(page.locator("#model-layer")).to_contain_class("opacity-10")
    expect(page.locator("#arrow-r-m-down")).to_contain_class("opacity-10")
    
    # Complete Run 2
    page.click("#nextBtn")  # 5
    page.click("#nextBtn")  # 6
    page.click("#nextBtn")  # 7
    expect(page.locator("#current-step-num")).to_have_text("7")
    
    # Complete Run 2
    page.click("#nextBtn")
    expect(page.locator("#r6-explanation-panel")).not_to_be_visible()
    
    # Verify both records are in the simulated database container
    db_text = page.locator("#database-content").inner_text()
    assert "First Student" in db_text
    assert "Second Student" in db_text

import os
import sys
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

INDEX_HTML_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../index.html")).replace("\\", "/")
INDEX_URL = f"file:///{INDEX_HTML_PATH}"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto(INDEX_URL)
    
    page.fill("#studentName", "Bob")
    page.click("#startBtn")
    
    # Step 1 is active. Go to Step 5
    for _ in range(4):
        page.click("#nextBtn")
        
    print("Current Step:", page.locator("#current-step-num").inner_text())
    print("R6 Input Text:")
    print(page.locator("#r6-class-input").inner_text())
    print("\nR6 Output Text:")
    print(page.locator("#r6-class-output").inner_text())
    
    # Go to Step 6
    page.click("#nextBtn")
    print("\n--- Step 6 ---")
    print("R6 Input Text:")
    print(page.locator("#r6-class-input").inner_text())
    print("R6 Output Text:")
    print(page.locator("#r6-class-output").inner_text())
    
    browser.close()

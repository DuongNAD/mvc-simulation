import os
import asyncio
import sys
from playwright.async_api import async_playwright

async def run_verification():
    html_path = os.path.abspath("index.html")
    file_url = f"file:///{html_path.replace(os.sep, '/')}"
    print(f"Opening URL: {file_url}")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context()
        # Grant clipboard read/write permissions to context
        await context.grant_permissions(["clipboard-read", "clipboard-write"])
        
        page = await context.new_page()
        
        # Capture console logs safely avoiding Windows encoding crashes
        page.on("console", lambda msg: print(f"[CONSOLE]: {msg.text.encode('ascii', errors='replace').decode('ascii')}"))
        page.on("pageerror", lambda err: print(f"[PAGE ERROR]: {err.message.encode('ascii', errors='replace').decode('ascii')}"))
        
        # 1. Open index.html
        await page.goto(file_url)
        print("Page loaded successfully.")
        
        # 2. Verify Initial State
        print("\n=== STEP 0: Initial State Verification ===")
        student_name = page.locator("#studentName")
        start_btn = page.locator("#startBtn")
        sim_controls = page.locator("#simulation-controls")
        code_panel = page.locator("#contextual-code-panel")
        db_content = page.locator("#database-content")
        
        assert await student_name.is_enabled()
        assert await start_btn.is_enabled()
        assert not await sim_controls.is_visible()
        assert not await code_panel.is_visible()
        assert "Database trống" in await db_content.inner_text()
        print("Initial state is correct.")
        
        # 3. Start Simulation
        print("\n=== Start Simulation ===")
        await student_name.fill("Tran Van B")
        await start_btn.click()
        
        # Wait for the visual changes to propagate
        await page.wait_for_timeout(300)
        
        # Verify disabled input and visible controls
        assert not await student_name.is_enabled()
        assert not await start_btn.is_enabled()
        assert await sim_controls.is_visible()
        assert await code_panel.is_visible()
        
        # Verify Step 1
        step_num = page.locator("#current-step-num")
        step_layer = page.locator("#current-step-layer")
        step_code = page.locator("#current-step-code")
        main_layer = page.locator("#main-layer")
        
        assert await step_num.inner_text() == "1"
        assert await step_layer.inner_text() == "Main.java"
        assert "active" in (await main_layer.get_attribute("class"))
        print("Step 1 (Main) is active and correct.")
        
        next_btn = page.locator("#nextBtn")
        prev_btn = page.locator("#prevBtn")
        
        # 4. Step 2 (Controller)
        await next_btn.click()
        await page.wait_for_timeout(100)
        assert await step_num.inner_text() == "2"
        assert await step_layer.inner_text() == "StudentController.java"
        assert "active" in (await page.locator("#controller-layer").get_attribute("class"))
        print("Step 2 (Controller) is active and correct.")
        
        # 5. Step 3 (Service)
        await next_btn.click()
        await page.wait_for_timeout(100)
        assert await step_num.inner_text() == "3"
        assert await step_layer.inner_text() == "StudentService.java"
        assert "active" in (await page.locator("#service-layer").get_attribute("class"))
        assert "active" in (await page.locator("#arrow-c-s-down").get_attribute("class"))
        print("Step 3 (Service) is active and correct.")
        
        # 6. Step 4 (Repository)
        await next_btn.click()
        await page.wait_for_timeout(100)
        assert await step_num.inner_text() == "4"
        assert await step_layer.inner_text() == "StudentService.java"
        assert "active" in (await page.locator("#repo-layer").get_attribute("class"))
        assert "active" in (await page.locator("#arrow-s-r-down").get_attribute("class"))
        print("Step 4 (Repository) is active and correct.")
        
        # 7. Step 5 (Model / Database add)
        await next_btn.click()
        await page.wait_for_timeout(100)
        assert await step_num.inner_text() == "5"
        assert await step_layer.inner_text() == "StudentRepository.java"
        assert "active" in (await page.locator("#model-layer").get_attribute("class"))
        assert "active" in (await page.locator("#arrow-r-m-down").get_attribute("class"))
        
        # Verify db contains the student Tran Van B
        assert "Tran Van B" in await db_content.inner_text()
        print("Step 5 (Model) is active, student added to DB successfully.")
        
        # 8. Step backwards to Step 4 (Rollback check)
        print("\n=== Database Rollback Check ===")
        await prev_btn.click()
        await page.wait_for_timeout(100)
        assert await step_num.inner_text() == "4"
        # Database content should be empty again
        assert "Database trống" in await db_content.inner_text()
        print("Database rolled back successfully! Verification passed.")
        
        # 9. Step forward to Step 5 again
        await next_btn.click()
        await page.wait_for_timeout(100)
        assert await step_num.inner_text() == "5"
        assert "Tran Van B" in await db_content.inner_text()
        
        # 10. Step 6 (Service / Controller response)
        await next_btn.click()
        await page.wait_for_timeout(100)
        assert await step_num.inner_text() == "6"
        assert await step_layer.inner_text() == "StudentService.java"
        print("Step 6 is active and correct.")
        
        # 11. Step 7 (View output)
        await next_btn.click()
        await page.wait_for_timeout(100)
        assert await step_num.inner_text() == "7"
        assert await step_layer.inner_text() == "StudentView.java"
        assert "active" in (await page.locator("#view-layer").get_attribute("class"))
        assert "Thêm sinh viên thành công" in await page.locator("#console-output").inner_html()
        print("Step 7 (View) is active and correct.")
        
        # 12. Complete simulation (Hoàn thành)
        await next_btn.click()
        await page.wait_for_timeout(200)
        # Verify reset state
        assert await student_name.is_enabled()
        assert await start_btn.is_enabled()
        assert not await sim_controls.is_visible()
        assert not await code_panel.is_visible()
        # Database must retain Tran Van B because simulation completed
        assert "Tran Van B" in await db_content.inner_text()
        print("Simulation completed and reset successfully. DB retained Tran Van B.")
        
        # 13. Source Code Tab Verification
        print("\n=== Source Code Tab Check ===")
        tab_source_btn = page.locator("#tab-source-btn")
        tab_source = page.locator("#tab-source")
        
        await tab_source_btn.click()
        await page.wait_for_timeout(200)
        assert await tab_source.is_visible()
        
        select_file = page.locator("#java-file-select")
        await select_file.select_option("StudentController")
        await page.wait_for_timeout(100)
        
        file_name_display = page.locator("#java-file-name")
        file_content_display = page.locator("#java-file-content")
        
        assert await file_name_display.inner_text() == "StudentController.java"
        assert "class StudentController" in await file_content_display.inner_text()
        print("Source Code tab select Controller successfully.")
        
        # Test copy button changes state
        copy_btn = page.locator("#copy-btn")
        await copy_btn.click()
        await page.wait_for_timeout(200)
        assert "Đã sao chép" in await copy_btn.inner_text()
        print("Copy button clicked and status changed successfully.")
        
        await browser.close()
        print("\n>>> ALL TESTS PASSED SUCCESSFULLY! <<<")

if __name__ == "__main__":
    asyncio.run(run_verification())

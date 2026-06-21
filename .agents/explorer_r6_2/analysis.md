# R6 Deep-Dive Explanation Panel & I/O Mapping Test Analysis

This document provides a detailed analysis of the existing python E2E and adversarial test suites (`tests/test_mvc_flow.py`, `tests/test_adversarial_ui.py`) and outlines the proposed test updates needed to verify the new requirement **R6: Deep-Dive Class Explanations & I/O Mapping** in the Java MVC Educational Simulation.

---

## 1. Executive Summary

Requirement **R6** introduces a dedicated UI explanation panel in `index.html` that displays:
1. **Real-World Purpose**: The role of the currently active class/file (e.g. `Main.java`, `StudentController.java`, etc.).
2. **Exact Input**: The data structure and values received by the class in the current step.
3. **Action & Output**: What the class is doing with the input data and the exact output data it is preparing to send.

To robustly verify R6 without breaking existing tests, we propose a comprehensive DOM contract and structured updates to both `test_mvc_flow.py` and `test_adversarial_ui.py` spanning all test tiers (DOM checks, initial state, boundary validation, step-by-step stepping forward/backward, consecutive run resets, HTML escaping, fast stepping, and programmatic bypasses).

---

## 2. Proposed UI/DOM Contract for R6

To maintain Playwright test stability and keep the implementation decoupled, we define the following DOM element contract for the R6 Explanation Panel:

| Element ID | Expected Role / Content | Initial State (Load / Reset) | Active State (Steps 1-7) |
|---|---|---|---|
| `#explanation-panel` | Container of the deep-dive explanation panel | Hidden (contains `hidden` class or not visible) | Visible (does not contain `hidden` class) |
| `#explanation-purpose` | Renders the real-world purpose of the active class | Empty or default placeholder | Populated with step-specific purpose explanation |
| `#explanation-input` | Renders the current exact input data structure/value | Empty or default placeholder | Populated with step-specific input payload |
| `#explanation-output` | Renders the action and outgoing data structure/value | Empty or default placeholder | Populated with step-specific output data |

---

## 3. Step-by-Step Expected Explanation Mappings

At each of the 7 steps, the explanation elements should contain the following details:

| Step | Active Class | Purpose (Keywords to Assert) | Input Data (Value/Structure) | Action & Output (Value/Structure) |
| :--- | :--- | :--- | :--- | :--- |
| **Step 1** | `Main.java` | `Main.java`, `entry point`, `nhập liệu` | Raw string name from keyboard input (e.g. `"Nguyễn Văn A"` or `"Bob"`) | Packages data into `StudentRequestDTO` |
| **Step 2** | `StudentController.java` | `StudentController.java`, `routes`, `điều phối` | `StudentRequestDTO` (containing the name) | Forwards `StudentRequestDTO` to the Service |
| **Step 3** | `StudentService.java` | `StudentService.java`, `nghiệp vụ`, `logic`, `validate` | `StudentRequestDTO` (containing the name) | Validates the name is not empty. Returns validated name. |
| **Step 4** | `StudentRepository.java` | `StudentRepository.java`, `kho dữ liệu`, `CRUD`, `database` | Validated student data (name) | Invokes Model Entity constructor and prepares query |
| **Step 5** | `Student.java` | `Student.java`, `Entity`, `thực thể`, `Model` | Raw fields (`id`, `name`, `createdAt`) | Instantiated persistent `Student` Entity |
| **Step 6** | `StudentService.java` / `StudentController.java` | `ResponseDTO`, `đóng gói`, `Service` / `Controller` | Saved `Student` Entity object | `StudentResponseDTO` containing ID, success msg, display string |
| **Step 7** | `StudentView.java` | `StudentView.java`, `View`, `hiển thị`, `presentation` | `StudentResponseDTO` | Renders formatted display string to the terminal console |

---

## 4. Proposed Test Updates

### A. Updates to `tests/test_mvc_flow.py`

#### 1. Polyfill Update (`polyfill_stepping_if_needed`)
To support backward compatibility for skeletal HTML test runs, we propose injecting placeholder elements for the R6 Explanation Panel if they are not natively present, and updating their content in the simulation steps.

**Proposed Change inside `polyfill_stepping_if_needed` JS evaluation block:**
```javascript
// Check and create explanation panel elements
if (!document.getElementById('explanation-panel')) {
    const expPanel = document.createElement('div');
    expPanel.id = 'explanation-panel';
    expPanel.className = 'hidden mt-4 p-4 bg-gray-800 text-white rounded-lg';
    
    const purpose = document.createElement('div');
    purpose.id = 'explanation-purpose';
    
    const inputData = document.createElement('div');
    inputData.id = 'explanation-input';
    
    const outputData = document.createElement('div');
    outputData.id = 'explanation-output';
    
    expPanel.appendChild(purpose);
    expPanel.appendChild(inputData);
    expPanel.appendChild(outputData);
    
    document.getElementById('main-layer').appendChild(expPanel);
}

// In window.simulationSteps array, update the values inside setup/cleanup functions:
// e.g. for Step 0 (Main.java):
setup: () => {
    // ... existing highlights ...
    const nameVal = document.getElementById('studentName').value;
    document.getElementById('explanation-panel').classList.remove('hidden');
    document.getElementById('explanation-purpose').innerText = "Main.java acts as the entry point reading keyboard input.";
    document.getElementById('explanation-input').innerText = "Input Name: " + nameVal;
    document.getElementById('explanation-output').innerText = "Output DTO: StudentRequestDTO { name: " + nameVal + " }";
},
cleanup: () => {
    // ... existing cleanups ...
    document.getElementById('explanation-panel').classList.add('hidden');
}
```

#### 2. Tier 1: DOM Elements Existence (`test_tier1_dom_elements_exist`)
Verify that the new explanation panel elements exist in the DOM on load.
```python
# Add to test_tier1_dom_elements_exist
expect(page.locator("#explanation-panel")).to_be_attached()
expect(page.locator("#explanation-purpose")).to_be_attached()
expect(page.locator("#explanation-input")).to_be_attached()
expect(page.locator("#explanation-output")).to_be_attached()
```

#### 3. Tier 1: Initial State (`test_tier1_initial_state`)
Verify that the explanation panel is hidden initially.
```python
# Add to test_tier1_initial_state
expect(page.locator("#explanation-panel")).not_to_be_visible()
```

#### 4. Tier 2: Validation Failure State (`test_tier2_empty_name_validation` & `test_tier2_whitespace_name_validation`)
Verify that the panel remains hidden when validation fails and prevents the simulation from starting.
```python
# Add to validation tests
expect(page.locator("#explanation-panel")).not_to_be_visible()
```

#### 5. Tier 3: Step-by-Step Stepping Flow (`test_tier3_manual_stepping_flow`)
Add assertions to verify the correctness of the explanation panel contents at all 7 steps (both polyfilled and native).

**Proposed Update for Native Assertions (`else:` block):**
Update the internal helper `assert_state` to receive the name input and inspect the explanation panel contents:
```python
        def assert_state(step: int, tracking_text: str, student_name: str):
            expect(page.locator("#file-tracking-display")).to_have_text(tracking_text)
            
            # Verify R6 Explanation Panel is visible during simulation
            expect(page.locator("#explanation-panel")).to_be_visible()
            
            purpose = page.locator("#explanation-purpose")
            input_val = page.locator("#explanation-input")
            output_val = page.locator("#explanation-output")
            
            expect(purpose).not_to_be_empty()
            expect(input_val).not_to_be_empty()
            expect(output_val).not_to_be_empty()
            
            # Step-specific assertion rules
            if step == 1:
                expect(purpose).to_contain_text("Main.java")
                expect(purpose).to_contain_text("nhập")
                expect(input_val).to_contain_text(student_name)
                expect(output_val).to_contain_text("StudentRequestDTO")
            elif step == 2:
                expect(purpose).to_contain_text("StudentController")
                expect(purpose).to_contain_text("điều phối")
                expect(input_val).to_contain_text("StudentRequestDTO")
                expect(output_val).to_contain_text("StudentRequestDTO")
            elif step == 3:
                expect(purpose).to_contain_text("StudentService")
                expect(purpose).to_contain_text("nghiệp vụ")
                expect(input_val).to_contain_text("StudentRequestDTO")
                expect(output_val).to_contain_text(student_name)
            elif step == 4:
                expect(purpose).to_contain_text("StudentRepository")
                expect(purpose).to_contain_text("kho dữ liệu")
                expect(input_val).to_contain_text(student_name)
                expect(output_val).to_contain_text("Student")
            elif step == 5:
                expect(purpose).to_contain_text("Student.java")
                expect(purpose).to_contain_text("thực thể")
                expect(input_val).to_contain_text("id")
                expect(input_val).to_contain_text(student_name)
                expect(output_val).to_contain_text("Student")
            elif step == 6:
                expect(purpose).to_contain_text("Service")
                expect(purpose).to_contain_text("ResponseDTO")
                expect(input_val).to_contain_text("Student")
                expect(output_val).to_contain_text("StudentResponseDTO")
            elif step == 7:
                expect(purpose).to_contain_text("StudentView")
                expect(purpose).to_contain_text("hiển thị")
                expect(input_val).to_contain_text("StudentResponseDTO")
                expect(output_val).to_contain_text("Thêm sinh viên thành công")
```
Call this helper at every step of the stepping flow:
```python
        # Step 1: Main active
        assert_state(1, "Main.java ➔ StudentRequestDTO.java", "Bob")
        # Step 2: Controller active
        page.click("#nextBtn")
        assert_state(2, "StudentRequestDTO.java ➔ StudentController.java", "Bob")
        # ... repeat for all 7 steps
```

#### 6. Tier 3: Stepping Backward (`test_tier3_manual_stepping_backward`)
Verify that stepping backward Reverts the explanation panel content to the previous step's state.
```python
        # Native backward assertion check:
        # Currently at Step 3, step back to Step 2:
        page.click("#prevBtn")
        expect(page.locator("#explanation-purpose")).to_contain_text("StudentController")
        expect(page.locator("#explanation-input")).to_contain_text("StudentRequestDTO")
```

#### 7. Tier 4: Reset & Accumulation (`test_tier4_multi_run_accumulation`)
Verify that when the simulation is finished, the explanation panel is hidden, and when restarted with a different student name, the panel correctly updates with the new name.
```python
        # After completing Run 1 (Daniel):
        expect(page.locator("#explanation-panel")).not_to_be_visible()
        
        # Start Run 2 (Emma):
        page.fill("#studentName", "Emma")
        page.click("#startBtn")
        
        # Verify explanation panel at Step 1 contains "Emma" instead of "Daniel"
        expect(page.locator("#explanation-input")).to_contain_text("Emma")
```

---

### B. Updates to `tests/test_adversarial_ui.py`

#### 1. HTML & XSS Injection escaping check (`test_adversarial_html_injection`)
Ensure that the text values injected into the explanation panel (like the student name in input/output sections) are properly escaped, and do not get rendered as actual HTML/XSS elements.
```python
    # Inside test_adversarial_html_injection
    injected_html = '<span id="xss-test">Injected Content</span>'
    page.fill("#studentName", injected_html)
    page.click("#startBtn")
    
    # Verify Step 1 input displays raw text but does not compile the tag in DOM
    injected_el_panel = page.locator("#explanation-panel #xss-test")
    assert injected_el_panel.count() == 0
    
    expect(page.locator("#explanation-input")).to_contain_text(injected_html)
```

#### 2. Fast Stepping consistency (`test_adversarial_fast_stepping`)
Verify that rapid clicks through all steps correctly sync the explanation panel.
```python
    # Inside test_adversarial_fast_stepping
    # After rapid next clicks to Step 7:
    expect(page.locator("#explanation-panel")).to_be_visible()
    expect(page.locator("#explanation-purpose")).to_contain_text("StudentView")
    
    # After rapid prev clicks to Step 1:
    expect(page.locator("#explanation-panel")).to_be_visible()
    expect(page.locator("#explanation-purpose")).to_contain_text("Main.java")
```

#### 3. Programmatic bypass robustness (`test_adversarial_boundary_bypass`)
Ensure that programmatic execution bypasses do not corrupt the explanation panel.
```python
    # Inside test_adversarial_boundary_bypass
    # At Step 1: programmatic prevStep() should keep explanation panel at Step 1:
    page.evaluate("prevStep()")
    expect(page.locator("#explanation-purpose")).to_contain_text("Main.java")
    
    # At Step 7: programmatic nextStep() completes simulation, panel must be hidden:
    page.evaluate("nextStep()")
    expect(page.locator("#explanation-panel")).not_to_be_visible()
```

---

## 5. Updates to `PROJECT.md`

We should propose updating the **Milestones** or **Interface Contracts** sections in `PROJECT.md` to reflect the completed state of **R6**.
Under the requirements section, add:
- `R6. Deep-Dive Class Explanations & I/O Mapping` - Added visual details on active class real-world purpose, exact input, and exact output data for all 7 steps.

---

## 6. Verification and Diagnostics

Once these test updates are implemented, the E2E suite can be verified by running the test runner command:
```powershell
python tests/run_tests.py
```
Or directly running pytest:
```powershell
pytest tests/
```
If the tests fail, it implies a defect in the implementation of the explanation panel inside `index.html`. If the tests pass, it confirms that all 7 steps correctly display the class purpose, inputs, and outputs in an escaped, robust manner.

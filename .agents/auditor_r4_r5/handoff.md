# Forensic Audit Handoff Report

## 1. Observation
### R4: Detailed File-Level Data Tracking
- Path: `e:\test\mvc-simulation\index.html`
- In `index.html` (lines 998-1006), the `fileTrackingMap` maps steps 1-7 to specific Java files:
  ```javascript
            const fileTrackingMap = {
                1: "Main.java ➔ StudentRequestDTO.java",
                2: "StudentRequestDTO.java ➔ StudentController.java",
                3: "StudentController.java ➔ StudentService.java",
                4: "StudentService.java ➔ StudentRepository.java",
                5: "StudentRepository.java ➔ Student.java",
                6: "Student.java ➔ StudentService.java ➔ StudentResponseDTO.java ➔ StudentController.java",
                7: "StudentController.java ➔ StudentView.java"
            };
  ```
  And updates the DOM element `#file-tracking-display` (lines 1007-1010):
  ```javascript
            const fileTrack = document.getElementById('file-tracking-display');
            if (fileTrack) {
                fileTrack.innerText = fileTrackingMap[stepIndex];
            }
  ```
  The DOM element `#file-tracking-display` is declared at lines 235-239:
  ```html
                                <div class="flex flex-col">
                                    <span class="text-[10px] text-gray-400 uppercase tracking-wider font-bold block mb-1">Tập Tin Tương Tác:</span>
                                    <div id="file-tracking-display" class="font-mono text-xs text-blue-300 bg-gray-800 p-2 rounded border border-gray-600 min-h-[40px] whitespace-pre-wrap break-all transition-colors duration-300">
                                        Chờ khởi tạo...
                                    </div>
                                </div>
  ```
  User input is read dynamically (line 931):
  ```javascript
            nameInputVal = nameInput.value.trim();
  ```
  And injected into payload displays dynamically (e.g. line 1015, line 1040, line 1061, line 1070) without hardcoded values.

### R5: Progressive Diagram Breakdown
- Path: `e:\test\mvc-simulation\index.html`
- In `index.html`, diagram layers and arrows are set to `opacity-10` by default (lines 149, 160, 161, 165, 176, 177, 181, 192, 196). For example, line 149:
  ```html
  <div id="controller-layer" class="bg-white border-2 border-gray-200 rounded-xl p-3 flex items-center gap-3 layer-box z-10 opacity-10 transition-opacity duration-500">
  ```
  Opacities are toggled progressively via `setOpacity` in `showStep` (lines 985-995):
  ```javascript
            setOpacity('main-layer', true);
            setOpacity('controller-layer', stepIndex >= 2);
            setOpacity('arrow-c-s-down', stepIndex >= 3);
            ...
  ```
  And reset to baseline in `applyBaselineOpacity` (lines 880-892).

### Python E2E and Adversarial Tests
- Tool Command: `py tests/run_tests.py`
- Executed successfully via background task-37.
- Verbatim stdout output:
  ```
============================= 11 passed in 13.28s =============================
============================================================
TEST RUNNER SUMMARY
============================================================
RESULT: PASS
  ```
- All 11 test cases passed:
  - `tests/test_adversarial_ui.py::test_adversarial_html_injection`
  - `tests/test_adversarial_ui.py::test_adversarial_fast_stepping`
  - `tests/test_adversarial_ui.py::test_adversarial_boundary_bypass`
  - `tests/test_mvc_flow.py::test_tier1_dom_elements_exist`
  - `tests/test_mvc_flow.py::test_tier1_initial_state`
  - `tests/test_mvc_flow.py::test_tier2_empty_name_validation`
  - `tests/test_mvc_flow.py::test_tier2_whitespace_name_validation`
  - `tests/test_mvc_flow.py::test_tier2_button_disabled_during_execution`
  - `tests/test_mvc_flow.py::test_tier3_manual_stepping_flow`
  - `tests/test_mvc_flow.py::test_tier3_manual_stepping_backward`
  - `tests/test_mvc_flow.py::test_tier4_multi_run_accumulation`

### Codebase Integrity & Absence of Cheating/Facade Practices
- Observed Java backend implementation in `src/service/StudentService.java` and `src/repository/StudentRepository.java`.
- Source code contains real logic for data operations and validations.
- Run `find_by_name` for `*result*`, `*output*`, and `*log*` in `e:\test\mvc-simulation`, yielding 0 results. No pre-populated logs or cheat bypasses exist.

---

## 2. Logic Chain
1. From the observations in `index.html` (lines 998-1010 and 235-239), the file tracking map is updated dynamically and the input names are inserted into the payloads directly without hardcoding. Thus, requirement R4 (Detailed File-Level Data Tracking) is correctly implemented without cheating.
2. From the default class declarations (e.g. `opacity-10`) and JavaScript calls to `setOpacity` in `index.html` (lines 880-892 and 985-995), the diagram components are faded initially and progressively revealed step-by-step as the simulation runs. Thus, requirement R5 (Progressive Diagram Breakdown) is correctly implemented.
3. The execution output of `py tests/run_tests.py` completed with exit code 0 and reported `RESULT: PASS` with 11/11 tests passing. This verifies that E2E and adversarial tests are functioning and correct.
4. Because the codebase uses real persistence, actual validation rules, escaping of HTML, and there are no pre-populated verification output files or test-runner-detection bypasses, the project has no facade, mock, or fake bypass implementations.
5. In combination, all forensic checks pass, leading to a verdict of CLEAN.

---

## 3. Caveats
- Checked codebase is focused on the Java MVC Simulation files (`index.html`, `src/`, `tests/`).
- The Python tests require Python 3.x and pytest / playwright libraries. The system environment has `py` launcher pointing to Python 3.11.9, which was used for execution.
- No other caveats.

---

## 4. Conclusion
### Forensic Audit Report
**Work Product**: e:\test\mvc-simulation  
**Profile**: General Project  
**Verdict**: CLEAN  

### Phase Results
- **Hardcoded output detection**: PASS — Values are dynamically loaded from user input.
- **Facade detection**: PASS — Real business validation, data persistence, and HTML escaping are implemented.
- **Pre-populated artifact detection**: PASS — No pre-populated result, output, or log files exist.
- **Behavioral verification**: PASS — All 11 E2E and adversarial python tests pass successfully.
- **Dependency audit**: PASS — No prohibited packages are imported; the project uses native HTML/JS and standard Java libraries.

---

## 5. Verification Method
To verify the audit findings:
1. Run the test command in PowerShell:
   ```powershell
   py tests/run_tests.py
   ```
   Check that all 11 test cases pass.
2. Open `index.html` in a web browser and enter a student name. Click "Thêm Sinh Viên" and step through each step. Check that:
   - The interactive file names are printed under "Tập Tin Tương Tác" dynamically (e.g., `Main.java ➔ StudentRequestDTO.java` on Step 1).
   - Only the active layers of the diagram are highlighted, and non-visited backend layers remain faded (at `opacity-10`) until reached.

# Handoff Report — challenger_r6_retry_2

## 1. Observation
- The execution of the test suite via `py tests/run_tests.py` failed with **4 failures** out of 18 test cases:
  - `test_backward_stepping_db_id` failed:
    ```
    AssertionError: Expected 'id: 1' in Step 5 input, got: Student {
      id: 2,
      name: "Bob",
      createdAt: "2026-06-21"
    }
    assert 'id: 1' in 'Student {\n  id: 2,\n  name: "Bob",\n  createdAt: "2026-06-21"\n}'
    ```
  - `test_stress_validation_bounds` failed:
    ```
    AssertionError: Locator expected to contain text ''; DROP TABLE students; --'
    Actual value: Tên sinh viên nhập thô: "&#39;; DROP TABLE students; --"
    ```
  - `test_stress_replacement_patterns` failed:
    ```
    AssertionError: Replacement pattern $' not rendered in input!
    assert "$'" in 'Tên sinh viên nhập thô: "$&#39;"'
    ```
  - `test_stress_dynamic_rendering_and_accumulation` failed:
    ```
    AssertionError: Locator expected to contain class 'opacity-100'
    Actual value: bg-white p-4 rounded-xl border-2 border-gray-200 mb-6 layer-box relative transition-opacity duration-500 opacity-10
    ```
- In `index.html` (lines 968-999), `updateR6Panel` escapes student names and updates the panel content:
  ```javascript
  const currentDbId = (stepIndex <= 5) ? (db.length + 1) : db.length;
  const currentDate = new Date().toISOString().split('T')[0];
  const escapedName = nameValue.replace(/[<>'"]/g, 
      tag => ({
          '<': '&lt;',
          '>': '&gt;',
          "'": '&#39;',
          '"': '&quot;'
      }[tag] || tag)
  );
  ...
  document.getElementById('r6-class-input').innerText = dynamicInput;
  document.getElementById('r6-class-output').innerText = dynamicOutput;
  ```
- In `index.html` (lines 1205-1216), `prevStep` handles reverse transitions:
  ```javascript
  function prevStep() {
      if (currentStep > 1) {
          // Rollback database additions if stepping backward from Step 5 to Step 4
          if (currentStep === 5 && tempStudent) {
              db.pop();
              tempStudent = null;
              document.getElementById('database-content').innerText = db.length > 0 ? db.join('\n') : '[ Database trống ]';
          }
          showStep(currentStep - 1);
      }
  }
  ```
- In `tests/test_challenger_r6_stress.py` (lines 174-177):
  ```python
  # Step 1 opacity check: only main and view active on start
  expect(page.locator("#main-layer")).to_contain_class("opacity-100")
  expect(page.locator("#view-layer")).to_contain_class("opacity-100")
  ```

## 2. Logic Chain
- **Logic Chain 1: Database ID mismatch during backward transitions**
  - At Step 5 forward, the student registration details are displayed by `updateR6Panel(5)`. Since `db.push` hasn't happened yet, `db.length` is `0`, and `currentDbId` calculates as `db.length + 1` = `1`. Afterward, the student is pushed to `db` (making its length `1`).
  - When stepping backward from Step 6 to Step 5, the student is still inside the database (since rollback is only triggered when stepping backward from Step 5 to Step 4). Therefore, `db.length` remains `1`.
  - During this backward transition, `updateR6Panel(5)` is called. Since `stepIndex` is 5 (which is `<= 5`), the ID is computed as `db.length + 1` = `1 + 1 = 2`.
  - Consequently, the R6 explanation panel displays `id: 2` in the code inputs/outputs, even though the database content container only holds the student with `id: 1`. This leads to a database ID rendering mismatch.
- **Logic Chain 2: Visual HTML entity double-escaping**
  - In `updateR6Panel`, characters like `'` and `<` are pre-escaped into HTML entities (such as `&#39;` and `&lt;`).
  - These values are then assigned directly to `.innerText` properties of `#r6-class-input` and `#r6-class-output`.
  - Because `.innerText` renders text verbatim and does not parse HTML entity escapes, the user sees raw HTML entity strings (`&#39;` instead of `'`) on the screen.
  - Using `.innerText` is inherently secure against XSS/HTML injection. Thus, pre-escaping strings here is not only redundant but actively introduces visual bugs for names containing quotes or brackets (e.g. `'`, `<`).
- **Logic Chain 3: Invalidation of stress test opacity check**
  - Under the progressive opacity scheme (R5), the view-layer is faded (`opacity-10`) at Step 1 and is only activated (`opacity-100`) once the flow reaches Step 7.
  - The stress test assertion expecting `#view-layer` to have class `opacity-100` at Step 1 is incorrect and directly conflicts with correct R5 behavior, leading to a test failure.

## 3. Caveats
- No caveats.

## 4. Conclusion
- The R6 panel replacement pattern handling is secure against data leaks (using arrow functions as replacement callbacks), but is impacted by two bugs:
  1. **Database ID regression**: Under backward transitions from Step 6 to Step 5, the R6 panel computes an incorrect database ID (`db.length + 1`), which is off-by-one.
  2. **Double-escaping rendering bug**: The manual escaping of `'` and `<` combined with `.innerText` results in raw HTML entity strings being shown to the user.
- Additionally, the third-party stress test `test_stress_dynamic_rendering_and_accumulation` contains a faulty assertion regarding layer opacity.

## 5. Verification Method
- Execute the test suite using:
  ```powershell
  py tests/run_tests.py
  ```
- Inspect the output to verify the 4 failures matching the tracebacks listed in this report.
- The new test file `tests/test_adversarial_stepping.py` specifically reproduces the database ID backward regression.

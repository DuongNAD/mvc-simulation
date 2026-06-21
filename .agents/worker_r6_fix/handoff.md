# Handoff Report — worker_r6_fix

## 1. Observation
- The baseline test execution of `py tests/run_tests.py` failed with 2 failures:
  - `test_adversarial_special_replacements_match` failed:
    ```
    E       AssertionError: R6 panel leaked 'Nguyễn Văn A' due to $& substitution!
    E       assert 'Nguyễn Văn A' not in 'Tên sinh vi...n Aamp; Bob"'
    ```
  - `test_adversarial_special_replacements_preceding` failed:
    ```
    E       AssertionError: R6 panel failed to render 'Alice $` Bob' correctly!
    E       assert 'Alice $` Bob' in 'Tên sinh viên nhập thô: "Alice Tên sinh viên nhập thô: " Bob"'
    ```
- In `index.html`, inside `updateR6Panel` (around line 968), the replacement uses literal strings as values:
  ```javascript
  let dynamicInput = data.input
      .replace(/Nguyễn Văn A/g, escapedName)
      .replace(/id: 1/g, `id: ${currentDbId}`)
      ...
  ```
- The step 5 database ID logic in `updateR6Panel` was using `(stepIndex <= 4)`:
  ```javascript
  const currentDbId = (stepIndex <= 4) ? (db.length + 1) : db.length;
  ```
  But `db.push` only occurs during the `case 5:` block of the simulation transition, which runs after `updateR6Panel` is called in `renderStep`. Thus, at step 5, `db.length` is still `0`, leading to a database ID calculation of `0` instead of the expected `1`.
- The `assert_state` helper in `tests/test_mvc_flow.py` (lines 606-610) asserted only the name `"Bob"` was in the input/output but did not check the database ID at each step.

## 2. Logic Chain
- In JavaScript's `.replace()` function, special character substitution patterns (like `$&` and `$``) in the second argument trigger special interpolation behavior based on the matched string. To avoid this and treat the replacement string strictly literally, we must pass an arrow function returning the replacement string (e.g. `() => escapedName`).
- Because `innerText` is used to write to the R6 panel elements, escaping `&` to `&amp;` causes the literal text `&amp;` to render in the browser. By defining a custom `escapedName` in `updateR6Panel` that only escapes `< > " '` but not `&`, we display `&` properly in plain text on the page while keeping the visual HTML representations safe for HTML injection.
- By changing the condition from `stepIndex <= 4` to `stepIndex <= 5`, Step 5 correctly uses `db.length + 1` for `currentDbId`, since the student has not yet been pushed to the database array at the time `updateR6Panel` is called.
- Adding targeted assertions in `tests/test_mvc_flow.py` inside the `assert_state` helper for steps 4 to 7 ensures that Playwright verifies the database ID `1` propagates properly through the R6 panel.

## 3. Caveats
- No caveats.

## 4. Conclusion
- The replace character substitution bug is resolved by passing arrow functions to the replace calls and keeping `&` unescaped for the `innerText` R6 panel fields.
- The step 5 database ID mismatch bug is resolved by changing the threshold to `(stepIndex <= 5)`.
- The test suite has been updated to check for correct database ID rendering at steps 4-7. All 13 tests now pass successfully.

## 5. Verification Method
- Execute the E2E test suite by running:
  ```powershell
  py tests/run_tests.py
  ```
- Verify that the output shows `13 passed`.
- Verify the code changes in:
  - `e:\test\mvc-simulation\index.html` (lines 968-998)
  - `e:\test\mvc-simulation\tests\test_mvc_flow.py` (lines 606-628)

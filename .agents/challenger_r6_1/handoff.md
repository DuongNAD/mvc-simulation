# Handoff Report — 2026-06-21T18:59:30+07:00

## 1. Observation
We ran the E2E test suite using the custom test runner via:
```powershell
py tests/run_tests.py
```
After adding `tests/test_adversarial_replacements.py` targeting special JavaScript replace pattern tokens, we observed the following test failures:

```
tests/test_adversarial_replacements.py::test_adversarial_special_replacements_match FAILED
tests/test_adversarial_replacements.py::test_adversarial_special_replacements_preceding FAILED

================================== FAILURES ===================================
_________________ test_adversarial_special_replacements_match _________________
...
>       assert "Nguyễn Văn A" not in input_text, "R6 panel leaked 'Nguyễn Văn A' due to $& substitution!"
E       AssertionError: R6 panel leaked 'Nguyễn Văn A' due to $& substitution!
E       assert 'Nguyễn Văn A' not in 'Tên sinh vi...n Aamp; Bob"'
E         
E         'Nguyễn Văn A' is contained here:
E           Tên sinh viên nhập thô: "Alice Nguyễn Văn Aamp; Bob"
E         ?                                ++++++++++++

_______________ test_adversarial_special_replacements_preceding _______________
...
>       assert "Alice $` Bob" in input_text, "R6 panel failed to render 'Alice $` Bob' correctly!"
E       AssertionError: R6 panel failed to render 'Alice $` Bob' correctly!
E       assert 'Alice $` Bob' in 'Tên sinh viên nhập thô: "Alice Tên sinh viên nhập thô: " Bob"'
```

### Affected File and Lines
The issue lies in `index.html` within the JavaScript helper function `updateR6Panel(stepIndex, nameValue)` (lines 968-992):
```javascript
968:         function updateR6Panel(stepIndex, nameValue) {
969:             const data = r6Explanations[stepIndex];
970:             if (!data) return;
971:             
972:             const currentDbId = (stepIndex <= 4) ? (db.length + 1) : db.length;
973:             const currentDate = new Date().toISOString().split('T')[0];
974:             const escapedName = escapeHTML(nameValue);
975:             
976:             let dynamicInput = data.input
977:                 .replace(/Nguyễn Văn A/g, escapedName)
978:                 .replace(/id: 1/g, `id: ${currentDbId}`)
979:                 .replace(/\[ID: 1\]/g, `[ID: ${currentDbId}]`)
980:                 .replace(/2026-06-21/g, currentDate);
981:                 
982:             let dynamicOutput = data.output
983:                 .replace(/Nguyễn Văn A/g, escapedName)
984:                 .replace(/id: 1/g, `id: ${currentDbId}`)
985:                 .replace(/\[ID: 1\]/g, `[ID: ${currentDbId}]`)
986:                 .replace(/2026-06-21/g, currentDate);
...
```

## 2. Logic Chain
1. When a user inputs a name containing special JavaScript replacement pattern symbols (e.g. `$&` or `` $` ``), these inputs bypass the baseline input validation because they are non-empty and non-whitespace-only strings.
2. In `updateR6Panel`, the user input is escaped via `escapeHTML(nameValue)` to produce `escapedName`. If the input is `Alice $& Bob`, the escaped string is `Alice $&amp; Bob`.
3. The function performs `data.input.replace(/Nguyễn Văn A/g, escapedName)`.
4. In JavaScript, when the second parameter of `String.prototype.replace()` is a string, character sequences starting with `$` are interpreted as special substitution tokens:
   - `$&` is replaced by the matched substring (which is the literal `"Nguyễn Văn A"`).
   - `` $` `` is replaced by the portion of the string preceding the matched substring.
5. Consequently, the replacement engine expands `$&amp;` into `Nguyễn Văn Aamp;`, resulting in `"Alice Nguyễn Văn Aamp; Bob"`. For `` $` ``, the replacement engine inserts the preceding part of `data.input`, resulting in `"Tên sinh viên nhập thô: "Alice Tên sinh viên nhập thô: " Bob"`.
6. This breaks the dynamic rendering layout of the R6 explanation panel and leaks the template placeholder `"Nguyễn Văn A"`.

## 3. Caveats
- No other security issues were observed: standard XSS payloads (such as `<script>alert(1)</script>`) are safely escaped in both the system console (`#console-output`) and the explanation panel because the application uses `escapeHTML` and inserts content via `.innerText` / safe DOM assignments.
- Stepping state machines (forward/backward), validation logic for empty names, and database rollbacks operate correctly as designed under adversarial fast clicking and bypass attempts.

## 4. Conclusion
The application suffers from a **Dynamic Rendering Injection / Character Substitution Defect** in the R6 Explanation Panel. When adversarial inputs matching JavaScript replacement patterns (e.g. `$&`, `` $` ``) are provided, the panel fails to render the student name accurately and leaks the template string `"Nguyễn Văn A"`.

### Recommended Mitigation
In `index.html`, pass a replacer function instead of a string to `String.prototype.replace()` to prevent interpretation of special replacement patterns:
```javascript
            let dynamicInput = data.input
                .replace(/Nguyễn Văn A/g, () => escapedName)
                .replace(/id: 1/g, () => `id: ${currentDbId}`)
                .replace(/\[ID: 1\]/g, () => `[ID: ${currentDbId}]`)
                .replace(/2026-06-21/g, () => currentDate);
```

## 5. Verification Method
1. Run the test runner script using the command:
   ```powershell
   py tests/run_tests.py
   ```
2. Assert that `tests/test_adversarial_replacements.py` fails on the current code base.
3. Apply the replacer function mitigation in `index.html` and re-run `py tests/run_tests.py` to verify that all 13 test cases pass successfully.

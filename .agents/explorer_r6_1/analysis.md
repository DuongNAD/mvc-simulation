# R6 Implementation Strategy: Deep-Dive Class Explanations & I/O Mapping

This document details the analysis and implementation strategy for requirement **R6 (Deep-Dive Class Explanations & I/O Mapping)** in the Java MVC Educational Simulation. 

---

## 1. Requirement Specification (R6)
At each step of the simulation, the UI must include a highly visible, dedicated explanation panel answering three core educational questions for the currently active class/file:
1. **Real-world purpose**: Plain, beginner-friendly explanation of why this class exists (e.g., "Why do we need a Service class instead of putting code in the Controller?").
2. **Exact Input Data**: Dynamic representation of the data the class/file is receiving in real-time, reflecting the actual user-input value (e.g. `Nguyễn Văn A`).
3. **Action and Exact Output Data**: Detailed action performed on the input and the exact data payload prepared for the next layer.

---

## 2. UI Layout Proposal (`index.html`)

### Position in DOM
The explanation panel will be placed in the **Simulation Tab (`#tab-simulation`)** within the left sub-column (below the **Backend Architecture Stack** and above the **Contextual Java Code Snippet panel**). This location ensures a natural reading flow:
1. **Top**: Visual architecture stack (progressive layer opacities).
2. **Middle**: Conceptual explanation, role details, and dynamic I/O mapping.
3. **Bottom**: Production-style Java code snippet matching the active class.

### Component Design (Tailwind CSS)
```html
<!-- Detailed Explanation Panel (R6) -->
<div id="explanation-panel" class="mt-6 bg-white rounded-xl shadow-sm border border-indigo-200 overflow-hidden flex flex-col hidden">
    <div class="bg-indigo-600 px-4 py-2 border-b border-indigo-700 flex items-center justify-between">
        <span class="text-xs font-bold text-white tracking-wider">PHÂN TÍCH CHI TIẾT BƯỚC <span id="explanation-step-num">0</span>: <span id="explanation-class-name" class="font-mono">TBD</span></span>
    </div>
    <div class="p-4 space-y-4">
        <!-- 1. Real-World Purpose -->
        <div>
            <h4 class="text-xs font-bold text-indigo-700 uppercase tracking-wider mb-1">1. Vai trò thực tế của lớp này là gì?</h4>
            <p id="explanation-purpose" class="text-sm text-gray-700 leading-relaxed"></p>
        </div>
        <!-- 2 & 3. Input & Output Side-by-Side -->
        <div class="border-t border-indigo-50 pt-3 flex flex-col md:flex-row gap-4">
            <div class="flex-1">
                <h4 class="text-xs font-bold text-indigo-700 uppercase tracking-wider mb-1">2. Dữ liệu Đầu vào (Input):</h4>
                <pre id="explanation-input" class="text-xs font-mono text-gray-600 bg-gray-50 p-2 rounded border border-gray-200 whitespace-pre-wrap min-h-[40px]"></pre>
            </div>
            <div class="flex-1">
                <h4 class="text-xs font-bold text-indigo-700 uppercase tracking-wider mb-1">3. Dữ liệu Đầu ra (Output) chuẩn bị:</h4>
                <pre id="explanation-output" class="text-xs font-mono text-gray-600 bg-gray-50 p-2 rounded border border-gray-200 whitespace-pre-wrap min-h-[40px]"></pre>
            </div>
        </div>
        <!-- Action Detail -->
        <div class="border-t border-indigo-50 pt-3">
            <h4 class="text-xs font-bold text-indigo-700 uppercase tracking-wider mb-1">Hành động thực thi (Action):</h4>
            <p id="explanation-action" class="text-sm text-gray-700 leading-relaxed"></p>
        </div>
    </div>
</div>
```

---

## 3. State Machine & Dynamic Mapping Strategy

A dynamic mapping mapping helper will be introduced into `index.html`'s `<script>` section. The text content and structural DTO/Entity maps will dynamically resolve the user's input (`nameInputVal`), the computed record ID, and the current date timestamp.

### JavaScript Data Structure

```javascript
// Dynamic resolver for R6 explanations
function getStepExplanation(stepIndex, nameInputVal, dbLength) {
    const currentDate = new Date().toISOString().split('T')[0];
    const nextId = dbLength + 1;
    const currentId = dbLength;

    const data = {
        1: {
            className: "Main.java",
            purpose: "Đóng vai trò là điểm khởi đầu (entry point) của ứng dụng console. Main chịu trách nhiệm cấu hình hệ thống, thiết lập liên kết giữa các tầng (Dependency Injection) và quản lý menu tương tác để nhận lệnh từ người dùng.",
            input: `Chuỗi ký tự từ giao diện:\n"${nameInputVal}"`,
            action: "Main kiểm tra cơ bản đầu vào để đảm bảo không rỗng, sau đó đóng gói giá trị nhập này vào một đối tượng Request DTO để chuyển tiếp.",
            output: `StudentRequestDTO {\n  name: "${nameInputVal}"\n}`
        },
        2: {
            className: "StudentController.java",
            purpose: "Là cửa ngõ tiếp nhận các yêu cầu (Request) từ client gửi tới backend. Controller điều hướng luồng đi bằng cách gọi tầng nghiệp vụ (Service) xử lý và gửi kết quả nhận được sang cho View hiển thị. Nó cô lập giao diện người dùng khỏi xử lý logic.",
            input: `StudentRequestDTO {\n  name: "${nameInputVal}"\n}`,
            action: "Controller nhận RequestDTO, mở khối try-catch bảo vệ hệ thống khỏi lỗi, rồi chuyển giao RequestDTO này sang Service xử lý nghiệp vụ.",
            output: `StudentRequestDTO {\n  name: "${nameInputVal}"\n}`
        },
        3: {
            className: "StudentService.java (Kiểm tra nghiệp vụ)",
            purpose: "Chứa toàn bộ logic nghiệp vụ (business rules) của hệ thống. Tách riêng Service giúp các quy tắc kiểm tra (như bắt buộc nhập tên) được tập trung một nơi, dễ bảo trì, độc lập với cơ sở dữ liệu và giao diện hiển thị.",
            input: `StudentRequestDTO {\n  name: "${nameInputVal}"\n}`,
            action: "Service kiểm tra tính hợp lệ của dữ liệu (Validate tên không rỗng bằng Validation.isBlank()). Nếu hợp lệ, chuyển giao dữ liệu xuống Repository.",
            output: `String name = "${nameInputVal}"`
        },
        4: {
            className: "StudentService.java ➔ StudentRepository.java",
            purpose: "Tách biệt giữa nghiệp vụ và lưu trữ. Service gọi phương thức Repository để lưu thực thể. Việc tách Repository giúp tầng nghiệp vụ độc lập hoàn toàn với việc cơ sở dữ liệu thực sự được tổ chức thế nào (SQL, file, RAM).",
            input: `String name = "${nameInputVal}"`,
            action: "Service gọi phương thức Repository addStudent(name) để thực hiện lưu trữ thông tin sinh viên vào Database.",
            output: `String name = "${nameInputVal}"`
        },
        5: {
            className: "StudentRepository.java & Student.java",
            purpose: "StudentRepository thực hiện lưu trữ dữ liệu thực tế vào Database. Student.java là thực thể Model Entity đại diện cho bảng dữ liệu trong DB. Tách Model giúp chuẩn hóa cấu trúc dữ liệu được lưu trữ.",
            input: `String name = "${nameInputVal}"`,
            action: "Repository khởi tạo đối tượng Student Entity mới, tự động gán ID tăng dần và ngày tạo hiện tại, rồi lưu vào cơ sở dữ liệu giả lập (Map).",
            output: `Student Entity {\n  id: ${nextId},\n  name: "${nameInputVal}",\n  createdAt: "${currentDate}"\n}`
        },
        6: {
            className: "StudentService.java & StudentResponseDTO.java",
            purpose: "StudentResponseDTO là đối tượng vận chuyển dữ liệu trả về cho client. Sử dụng ResponseDTO giúp bảo vệ thông tin nhạy cảm của Model Entity (như mật khẩu, ngày tạo nội bộ) và tránh việc View vô tình sửa đổi thực thể Database trực tiếp.",
            input: `Student Entity {\n  id: ${currentId},\n  name: "${nameInputVal}",\n  createdAt: "${currentDate}"\n}`,
            action: "Service nhận thực thể đã lưu thành công từ Repository, ánh xạ các trường cần thiết sang ResponseDTO kèm thông báo thành công và trả lại cho Controller.",
            output: `StudentResponseDTO {\n  id: ${currentId},\n  message: "Thành công!",\n  displayString: "[ID: ${currentId}] ${nameInputVal}"\n}`
        },
        7: {
            className: "StudentView.java",
            purpose: "Chỉ chịu trách nhiệm hiển thị kết quả cho người dùng. View không chứa bất kỳ logic nghiệp vụ nào, chỉ nhận ResponseDTO từ Controller và in ra màn hình. Nhờ đó, ta có thể đổi giao diện (từ console sang web/app) mà không sửa code backend.",
            input: `StudentResponseDTO {\n  id: ${currentId},\n  message: "Thành công!",\n  displayString: "[ID: ${currentId}] ${nameInputVal}"\n}`,
            action: "View nhận ResponseDTO, trích xuất chuỗi hiển thị và in thông điệp thành công cùng thông tin sinh viên ra màn hình Console.",
            output: `Console Render:\n> [GIAO DIỆN HỆ THỐNG]\n> Thêm sinh viên thành công!\n> Dữ liệu từ ResponseDTO: [ID: ${currentId}] Tên: ${nameInputVal}`
        }
    };
    return data[stepIndex];
}
```

### Integration into State Machine Callbacks

1. **`runSimulation()` Modification**:
   - Ensure the panel is made visible when the simulation is triggered:
     ```javascript
     document.getElementById('explanation-panel').classList.remove('hidden');
     ```

2. **`showStep(stepIndex)` Modification**:
   - Dynamically fetch the mapped content using `getStepExplanation` and populate the fields:
     ```javascript
     const explanation = getStepExplanation(stepIndex, nameInputVal, db.length);
     document.getElementById('explanation-step-num').innerText = stepIndex;
     document.getElementById('explanation-class-name').innerText = explanation.className;
     document.getElementById('explanation-purpose').innerText = explanation.purpose;
     document.getElementById('explanation-input').innerText = explanation.input;
     document.getElementById('explanation-output').innerText = explanation.output;
     document.getElementById('explanation-action').innerText = explanation.action;
     ```

3. **`completeSimulation()` Modification**:
   - Hide the explanation panel when the simulation completes:
     ```javascript
     document.getElementById('explanation-panel').classList.add('hidden');
     ```

4. **`resetUI()` Modification**:
   - Reset the panel elements to baseline text:
     ```javascript
     document.getElementById('explanation-step-num').innerText = "0";
     document.getElementById('explanation-class-name').innerText = "TBD";
     document.getElementById('explanation-purpose').innerText = "";
     document.getElementById('explanation-input').innerText = "";
     document.getElementById('explanation-output').innerText = "";
     document.getElementById('explanation-action').innerText = "";
     ```

---

## 4. E2E and Adversarial Testing Strategy

The E2E tests must be extended to verify that the explanation panel exists, becomes visible, correctly displays the dynamic input/output values including the student name, and hides itself when expected.

### Test Additions (`tests/test_mvc_flow.py`)
Add a new E2E test `test_tier3_explanation_panel_visibility_and_content` checking:
1. Initial state (hidden).
2. Visibility and correct content updates for each of the 7 simulation steps.
3. Proper cleanup on completing the simulation.

```python
def test_tier3_explanation_panel_visibility_and_content(page: Page):
    """Verify R6 explanation panel visibility, step updates, and dynamic text content matching the student name."""
    page.goto(INDEX_URL)
    
    # 1. Assert initial state (panel is hidden)
    expect(page.locator("#explanation-panel")).to_contain_class("hidden")
    
    # 2. Start simulation
    student_name = "Frank"
    page.fill("#studentName", student_name)
    page.click("#startBtn")
    
    # 3. Assert panel is visible
    expect(page.locator("#explanation-panel")).not_to_contain_class("hidden")
    
    # 4. Step-by-Step validation (Steps 1 to 7)
    expected_classes = {
        1: "Main.java",
        2: "StudentController.java",
        3: "StudentService.java (Kiểm tra nghiệp vụ)",
        4: "StudentService.java ➔ StudentRepository.java",
        5: "StudentRepository.java & Student.java",
        6: "StudentService.java & StudentResponseDTO.java",
        7: "StudentView.java"
    }
    
    for step in range(1, 8):
        # Verify step indicators
        expect(page.locator("#explanation-step-num")).to_have_text(str(step))
        expect(page.locator("#explanation-class-name")).to_have_text(expected_classes[step])
        
        # Verify non-empty purpose & action
        expect(page.locator("#explanation-purpose")).not_to_be_empty()
        expect(page.locator("#explanation-action")).not_to_be_empty()
        
        # Verify dynamic inputs/outputs contain the input name
        input_text = page.locator("#explanation-input").inner_text()
        output_text = page.locator("#explanation-output").inner_text()
        
        if step in [1, 2, 3, 4, 5]:
            assert student_name in input_text
        if step in [1, 2, 5, 6, 7]:
            assert student_name in output_text
            
        # Step forward unless it is the last step
        if step < 7:
            page.click("#nextBtn")
            
    # 5. Complete simulation and check if panel hides
    page.click("#nextBtn") # Click complete
    expect(page.locator("#explanation-panel")).to_contain_class("hidden")
```

### Adversarial Tests (`tests/test_adversarial_ui.py`)
Add assertions inside `test_adversarial_boundary_bypass` and `test_adversarial_fast_stepping` to confirm:
- Rapid stepping updates the explanation panel content accurately without lagging.
- Validation failures (e.g. submitting empty inputs) prevent the explanation panel from displaying.

---

## 5. Layout and Structural Compliance
- All new files, reports, and agent logs are stored strictly inside `.agents/explorer_r6_1/`.
- No changes to `src/` (production-style Java code) are required, preserving the compilable reference backend.
- There are no layout violations.

---

## 6. Action Plan for Implementer
1. **HTML Modification**: Insert the `#explanation-panel` block inside `index.html`'s left panel column.
2. **Javascript Modification**: Insert `getStepExplanation` helper, modify `runSimulation`, `showStep`, `completeSimulation`, and `resetUI` to update the panel contents dynamically.
3. **E2E & Adversarial Tests update**: Update `tests/test_mvc_flow.py` and `tests/test_adversarial_ui.py` with Playwright assertions verifying the new panel.
4. **Execution**: Run `pytest` via the test runner to verify everything compiles, passes, and complies with R6.

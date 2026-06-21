# Milestone 1: Environment & Codebase Discovery Report

## 1. Observation
The following details were observed directly in the workspace `e:\test\mvc-simulation`:

### A. Environment Capabilities
- **Python Version**: Executable `py` runs `Python 3.11.9`.
- **JDK/Compilers**: `java` version is `25` (LTS) and `javac` is `25`.
- **Python Packages**: 
  - `playwright` (version 1.60.0) is installed.
  - `pytest` (version 9.1.0) is installed.
  - `selenium` and `beautifulsoup4` (or `bs4`) are **not** installed.
- **Browsers**: Playwright has browser binaries installed in `C:\Users\Admin\AppData\Local\ms-playwright`. Only `chromium-1223` (along with `chromium_headless_shell-1223`, `ffmpeg-1011`, and `winldd-1007`) is present on disk.

### B. Existing index.html
- **Location**: `e:\test\mvc-simulation\index.html`
- **Language**: Vietnamese (`lang="vi"`)
- **Structure**: 
  - Left panel: Input main layer (`#main-layer` / `#studentName` / `#startBtn`) and output view layer (`#view-layer` / `#console-output`).
  - Right panel: Architectural stack (`#controller-layer`, `#service-layer`, `#repo-layer`, `#model-layer` / `#database-content`) and a live payload monitor (`#payload-display`, `#monitor-explanation`).
  - Style definitions: CSS styles `.layer-box.active`, `.arrow-down.active`, and `.arrow-up.active` define highlight states with color transitions.
- **Visual Flow**:
  - The script manages an in-memory array `const db = []`.
  - Clicking "Thêm Sinh Viên" invokes `runSimulation()`, which sequentially activates layers (`#main-layer`, `#controller-layer`, etc.) and arrows using `await delay(...)` statements.
  - The simulation currently operates under a mock "Student" scenario (`StudentRequestDTO`, `StudentEntity`, `StudentResponseDTO`).

### C. Existing Java Codebase
- **Location**: `e:\test\mvc-simulation\src/`
- **Scenario mismatch**: All files in `src/` represent a "Doctor" mock scenario:
  - `controller/DoctorController.java`
  - `dto/DoctorRequestDTO.java`
  - `dto/DoctorResponseDTO.java`
  - `model/Doctor.java`
  - `repository/DoctorRepository.java`
  - `view/DoctorView.java`
  - `main/Main.java`
  - `constants/Constants.java`, `constants/Message.java`
  - `utils/Validation.java`
- **Architectural gap**: There is **no Service layer** in the existing codebase. The `DoctorController` directly instantiates and interacts with `DoctorRepository` and `DoctorView`.

---

## 2. Logic Chain
1. **Testing Infrastructure Choice**: Playwright and Pytest are the only requested automation packages installed in the environment (Selenium and Beautifulsoup4 are missing). Thus, the E2E test suite in Milestone 2 must be developed using Playwright with Pytest as the test runner, targeting Chromium.
2. **Interactive Flow Stepping**: The current `runSimulation` in `index.html` runs entirely on automated delays (`await delay(1200)`, etc.). To add "Next Step" and "Previous Step" controls, we need to introduce a state machine (with a step index tracking variable `currentStep` from 0 to 7) to replace/supplement the automated timer loop.
3. **Database Consistency**: When stepping manually, database persistence occurs at Step 5. If a user steps forward into Step 5, the student should be pushed to the mock database. If they step backward into Step 4, that student must be popped out of the database to prevent duplicate/ghost data and preserve UI fidelity.
4. **Java Codebase Transition**: The current Java files model a "Doctor" scenario with no Service layer, while the frontend visualization models a "Student" scenario with a Service layer. To align the backend codebase with the frontend visualization, we must rename/rewrite all Java files to "Student" versions and introduce `StudentService` to enforce the complete `Controller ↔ Service ↔ Repository ↔ Model` architecture.

---

## 3. Caveats
- No other browser versions (such as Firefox or WebKit) are installed under `ms-playwright`. Tests must be configured to run on Chromium.
- Assumes the database rollback mechanism during stepping (popping the last pushed element) is sufficient for a linear single-entity addition flow. If multiple entities could be added concurrently in the visualization, a more complex transaction history would be required.

---

## 4. Conclusion

### A. Next/Previous Step Button Strategy for index.html
We will introduce manual stepping controls to control the state machine.

#### UI Modifications
Add a hidden controls container under the name input in `#main-layer` that contains the navigation buttons:
```html
<div id="simulation-controls" class="hidden mt-4 flex gap-2">
    <button id="prevBtn" onclick="prevStep()" class="flex-1 bg-gray-500 hover:bg-gray-600 text-white font-medium py-2 px-4 rounded-lg transition-colors">
        Trước
    </button>
    <button id="nextBtn" onclick="nextStep()" class="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-lg transition-colors">
        Sau
    </button>
</div>
```

#### JavaScript State-Machine Design
We will define `currentStep` (0 = Idle, 1 to 7 = Steps) and `nameInputVal`. Clicking "Thêm Sinh Viên" starts the manual mode by verifying name, disabling main input, showing `#simulation-controls`, setting `currentStep = 1`, and rendering Step 1.
```javascript
let currentStep = 0;
let nameInputVal = '';
let tempStudent = null; // Tracks uncommitted student in Step 5

function showStep(stepIndex) {
    resetUIForStep();
    currentStep = stepIndex;
    
    // Manage navigation button states
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    prevBtn.disabled = (stepIndex === 1);
    nextBtn.innerText = (stepIndex === 7) ? "Hoàn thành" : "Sau";
    
    switch(stepIndex) {
        case 1:
            document.getElementById('main-layer').classList.add('active');
            updatePayload(`StudentRequestDTO {\n  name: "${nameInputVal}"\n}`, "Tầng Main đóng gói dữ liệu nhập từ bàn phím thành RequestDTO.");
            break;
        case 2:
            document.getElementById('controller-layer').classList.add('active');
            document.getElementById('controller-status').innerHTML = `<span class="text-blue-600 font-semibold">Đã nhận RequestDTO từ Main</span>`;
            updatePayload(`StudentRequestDTO {\n  name: "${nameInputVal}"\n}`, "Controller nhận RequestDTO. Sắp tới sẽ truyền nó cho Service.");
            break;
        case 3:
            document.getElementById('arrow-c-s-down').classList.add('active');
            document.getElementById('service-layer').classList.add('active');
            document.getElementById('service-status').innerHTML = `<span class="text-yellow-600 font-semibold">Validate RequestDTO: Hợp lệ!</span>`;
            updatePayload(`StudentRequestDTO {\n  name: "${nameInputVal}"\n}`, "Service nhận RequestDTO để kiểm tra logic (Tên không rỗng, v.v.).");
            break;
        case 4:
            document.getElementById('arrow-s-r-down').classList.add('active');
            document.getElementById('repo-layer').classList.add('active');
            document.getElementById('repo-status').innerHTML = `<span class="text-green-600 font-semibold">Nhận RequestDTO, chuẩn bị CREATE...</span>`;
            updatePayload(`StudentRequestDTO {\n  name: "${nameInputVal}"\n}`, "Repository nhận RequestDTO, chuẩn bị map dữ liệu sang Model.");
            break;
        case 5:
            document.getElementById('arrow-r-m-down').classList.add('active');
            document.getElementById('model-layer').classList.add('active');
            const newId = db.length + 1;
            const currentDate = new Date().toISOString().split('T')[0];
            updatePayload(`StudentEntity {\n  id: ${newId},\n  name: "${nameInputVal}",\n  createdAt: "${currentDate}"\n}`, "Repository trích xuất dữ liệu từ RequestDTO và map thành Model/Entity chuẩn để lưu vào Database.");
            
            // Add student dynamically only once
            if (!tempStudent) {
                tempStudent = `{ id: ${newId}, name: "${nameInputVal}" }`;
                db.push(tempStudent);
                document.getElementById('database-content').innerText = db.join('\n');
            }
            break;
        case 6:
            document.getElementById('repo-layer').classList.add('active');
            document.getElementById('arrow-r-s-up').classList.add('active');
            document.getElementById('service-layer').classList.add('active');
            document.getElementById('arrow-s-c-up').classList.add('active');
            document.getElementById('controller-layer').classList.add('active');
            document.getElementById('controller-status').innerHTML = `<span class="text-blue-600 font-semibold">Tạo ResponseDTO để gọi View</span>`;
            
            const responseId = db.length;
            updatePayload(`StudentResponseDTO {\n  id: ${responseId},\n  message: "Thành công!",\n  displayString: "[ID: ${responseId}] ${nameInputVal}"\n}`, "Controller đóng gói kết quả vào ResponseDTO.");
            break;
        case 7:
            document.getElementById('view-layer').classList.add('active');
            updatePayload(`Giao tiếp hoàn tất!`, "View chỉ nhận ResponseDTO từ Controller và in ra màn hình.");
            
            const viewId = db.length;
            const consoleOut = document.getElementById('console-output');
            consoleOut.classList.replace('text-green-400', 'text-white');
            consoleOut.innerHTML = `> [GIAO DIỆN HỆ THỐNG]<br>> Thêm sinh viên thành công!<br>> Dữ liệu từ ResponseDTO: [ID: ${viewId}] Tên: ${nameInputVal}`;
            break;
    }
}

function nextStep() {
    if (currentStep === 7) {
        completeSimulation();
    } else {
        showStep(currentStep + 1);
    }
}

function prevStep() {
    if (currentStep > 1) {
        // Rollback DB entry if stepping backward from Step 5
        if (currentStep === 5 && tempStudent) {
            db.pop();
            tempStudent = null;
            document.getElementById('database-content').innerText = db.length > 0 ? db.join('\n') : '[ Database trống ]';
        }
        showStep(currentStep - 1);
    }
}

function completeSimulation() {
    // Commit simulation changes
    tempStudent = null; 
    currentStep = 0;
    
    // Hide controls & Re-enable Inputs
    document.getElementById('simulation-controls').classList.add('hidden');
    document.getElementById('studentName').disabled = false;
    document.getElementById('studentName').value = '';
    
    const btn = document.getElementById('startBtn');
    btn.disabled = false;
    btn.classList.remove('opacity-50', 'cursor-not-allowed');
    resetUI();
}
```

### B. Java Codebase Transformation Plan
The following files in `src/` should be renamed, rewritten, or created to transition from "Doctor" to the "Student Management System" scenario:

1. **Rename & Rewrite DTOs**:
   - `src/dto/DoctorRequestDTO.java` → `src/dto/StudentRequestDTO.java`
     - Fields: `private String name;`
   - `src/dto/DoctorResponseDTO.java` → `src/dto/StudentResponseDTO.java`
     - Fields: `private int id;`, `private String message;`, `private String displayString;`
2. **Rename & Rewrite Model**:
   - `src/model/Doctor.java` → `src/model/Student.java`
     - Fields: `private int id;`, `private String name;`, `private String createdAt;`
3. **Rename & Rewrite Repository**:
   - `src/repository/DoctorRepository.java` → `src/repository/StudentRepository.java`
     - Fields: `private Map<Integer, Student> studentMap;`, `private int idCounter = 1;`
     - Operations: `addStudent`, `deleteStudent`, `searchStudents`, `exists`, `isEmpty`.
4. **Create New Service Layer**:
   - `src/service/StudentService.java`
     - Fields: `private StudentRepository studentRepository;`
     - Handles business validations (name length, emptiness) and orchestrates maps between DTOs and Model Entities.
5. **Rename & Rewrite Controller**:
   - `src/controller/DoctorController.java` → `src/controller/StudentController.java`
     - Fields: `private StudentService studentService;`, `private StudentView studentView;`
     - Methods: `addStudent(StudentRequestDTO)`, `deleteStudent(int)`, `searchStudent(String)`.
6. **Rename & Rewrite View**:
   - `src/view/DoctorView.java` → `src/view/StudentView.java`
     - Renders lists of `StudentResponseDTO` objects into console tables.
7. **Rewrite Main Entry & Messages**:
   - `src/main/Main.java`: Updates scanner input handling to get Student name / ID.
   - `src/constants/Message.java`: Updates text constants to Student context (e.g. MENU choices: 1. Add Student, 2. Delete Student, 3. Search Student, 4. Exit).

### C. Milestone 2 Test Suite Setup (E2E Tests)
The tests will be organized under a new file `tests/test_mvc_flow.py` run via pytest.

- **Test Tier 1: Happy Paths & Basic Interactions**
  - *Initial DOM State*: Verify default values, visibility of elements, input is empty, and simulation buttons are hidden/disabled.
  - *Input Validation Check*: Submit an empty name input, assert that the error message is displayed and the simulation does not activate.
  - *Simulation Start*: Input name "Alice", click "Thêm Sinh Viên", verify inputs are disabled and step controls appear at Step 1.
- **Test Tier 2: Manual Navigation & State Machine Checks**
  - *Stepping Forward*: Perform sequential clicks on "Sau" from Step 1 to Step 7. Verify `.active` is added/removed on each layer in sequence, and that the payload displays matches:
    - Step 1: `StudentRequestDTO` payload.
    - Step 5: `StudentEntity` payload with assigned ID.
    - Step 6: `StudentResponseDTO` payload.
    - Step 7: Final View output with success text.
  - *Stepping Backward*: Click "Trước" from Step 5 to Step 4. Assert that the database view `#database-content` is cleared of the student record.
  - *Stepping Boundaries*: Clicking "Trước" at Step 1 keeps the state at Step 1. Clicking "Sau" (labeled "Hoàn thành") at Step 7 resets the simulation back to Idle.
- **Test Tier 3: Visual Arrow & Style Class Integrity**
  - Assert that connector arrows (`#arrow-c-s-down`, `#arrow-s-r-down`, etc.) correctly gain the `.active` class when transitioning between layers.
- **Test Tier 4: Consecutive Runs & Cumulative Database State**
  - Add "Student A" successfully. Run a second simulation to add "Student B". Assert that the Database display shows both records, verifying that the database accumulates states across runs.

---

## 5. Verification Method
To verify the environment capability claims:
1. Run `py --version` to confirm Python 3.11+.
2. Run `javac -version` to confirm JDK compiler version 25+.
3. Run `py -m pytest --version` to confirm pytest is installed.
4. Run `py -c "import playwright; print(playwright.__version__)"` to verify Playwright installation.
5. Search for Chromium folder under `C:\Users\Admin\AppData\Local\ms-playwright` to confirm browsers are ready.

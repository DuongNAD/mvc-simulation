# Project: Java MVC Educational Simulation

## Architecture
The application is an educational simulation designed to explain the Model-View-Controller (MVC) architecture using a Student Management System mock scenario. It consists of:
1. **Frontend Simulation (`index.html`)**: An interactive, web-based visualization depicting data flow through the MVC layers (View ↔ Controller ↔ Service ↔ Repository ↔ Model) with step-by-step navigation and active code snippet rendering.
2. **Backend Codebase (`src/`)**: A Java console application matching the Student Management System mock scenario to provide a real, compilable reference implementation of the simulation's concepts.
3. **Detailed File-Level Data Tracking (R4)**: Displays specific interacting Java files at each step inside the Live Payload Monitor (`#file-tracking-display`), mapping UI transitions directly to Java classes.
4. **Progressive Diagram Breakdown (R5)**: Dynamically controls layer and arrow opacities (faded to `opacity-10` by default, revealed to `opacity-100` when reached) to guide the student visually.
5. **Deep-Dive Class Explanations & I/O Mapping (R6)**: At each step, a dedicated explanation panel (`#r6-explanation-panel`) answers: (1) class purpose, (2) current input data structure, and (3) output/actions.

## Code Layout
- `index.html` - Interactive web page containing visualization, explanations, and code snippets.
- `src/` - Production-style Java classes.
  - `constants/` - System constants and message formats.
  - `dto/` - `StudentRequestDTO` (input data carrier) and `StudentResponseDTO` (output data carrier).
  - `model/` - `Student.java` representing the database entity.
  - `repository/` - `StudentRepository.java` simulating database storage and CRUD queries.
  - `service/` - `StudentService.java` executing validation and business logic.
  - `controller/` - `StudentController.java` routing requests and generating response DTOs.
  - `view/` - `StudentView.java` rendering outcomes.
  - `main/` - `Main.java` entry point running the console application menu.
  - `utils/` - Helper and validation utilities.
- `tests/` - Python automated E2E and unit test suite.
  - `run_tests.py` - Custom test runner discovering all test cases.
  - `test_mvc_flow.py` - Validates visualization states and DOM assertions.

## Milestones
| # | Name | Scope | Dependencies | Status |
|---|------|-------|-------------|--------|
| 1 | System Discovery | Analyze environment capabilities, browser tools, and setup test runner. | None | DONE |
| 2 | Test Infra & Suite | E2E Testing Track: Design test suite, write test runner and HTML/DOM validators (Tiers 1-4). Publish `TEST_READY.md`. | M1 | DONE |
| 3 | Interactive Flow & UI | Implementation Track: Implement "Next/Prev Step" buttons in `index.html` to manually control the MVC transition flow. | M1 | DONE |
| 4 | Java Snippets & Reference | Implementation Track: Embed and display contextual Java code snippets in `index.html` matching each step, and rewrite Java `src` code to match the Student scenario. | M3 | DONE |
| 5 | E2E Integration | Implementation Track: Validate full E2E test suite compliance and fix failures. | M2, M4 | DONE |
| 6 | Adversarial Hardening | Phase 2: Challenger-driven edge-case checking of the UI state machine. | M5 | DONE |
| 7 | Forensic Audit | Validate authenticity and integrity of implementation. | M6 | DONE |
| 8 | Detailed File-Level Tracking | Implement R4: Visual tracker for Java files interacting at each step. | M7 | DONE |
| 9 | Progressive Diagram Breakdown | Implement R5: Faded layers and arrows progressively revealed. | M8 | DONE |
| 10 | Handoff & Final Validation (Previous) | Verify all E2E tests, update documentation, and hand over the system for R4 & R5. | M9 | DONE |
| 11 | R6 Design | Design Split-View layout, step explanations, and dynamic parameter resolver for R6. | M10 | DONE |
| 12 | R6 UI Implementation | Implement #r6-explanation-panel alongside code snippet in index.html. | M11 | DONE |
| 13 | R6 Test Suite Extension | Extend E2E and adversarial tests with special replacements tests. | M12 | DONE |
| 14 | E2E Verification & Challenger Hardening | Run challenger tests, verify bounds, unicode, SQL injection, and reverse stepping. | M13 | DONE |
| 15 | Forensic Audit for R6 | Run Forensic Auditor to verify authenticity and integrity of R6 implementation. | M14 | DONE |
| 16 | Final Handoff & Validation | Verify all 18 tests, update root documentation, and deliver the system. | M15 | DONE |

## Interface Contracts
### StudentRequestDTO
- `String getName()` / `void setName(String name)`
### StudentResponseDTO
- `int getId()`, `String getMessage()`, `String getDisplayString()`
### StudentController
- `void addStudent(StudentRequestDTO requestDTO)` -> Calls Service layer to validate and persist.
- `void deleteStudent(int id)` -> Calls Service layer to remove.
- `void searchStudent(String query)` -> Calls Service to find and triggers View display.

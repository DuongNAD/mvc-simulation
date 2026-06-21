# Project Plan - Java MVC Educational Simulation

## Overview
We are building an interactive web-based educational simulation of the Java MVC architecture. The simulation uses a Student Management System mock scenario to show data flow between layers and displays corresponding reference Java code snippets.

## Plan Steps
1. **Assessment & Discovery (Milestone 1)**
   - Spawn an Explorer to inspect the workspace environment, check available python libraries (like playwright, selenium, bs4), check browser availability, and check java compiler options.
2. **Test Infrastructure & Dual Track Setup (Milestone 2)**
   - Create E2E test runner and test cases in `tests/` covering:
     - Tier 1: Happy-path load and transition checks.
     - Tier 2: Boundary/edge input validation and button states.
     - Tier 3: Interactive state combinations and reset flows.
     - Tier 4: Real-world Student Management System workflow scenarios.
   - Publish `TEST_READY.md`.
3. **Interactive Visual Flow Implementation (Milestone 3)**
   - Update `index.html` to implement step-by-step interactive flow using "Next Step" / "Previous Step" buttons.
   - Ground the flow in a Student Management System scenario, clearly showing data movement through View -> Controller -> Service -> Repository -> Model -> Repository -> Service -> Controller -> View.
4. **Reference Java Code Snippets Integration (Milestone 4)**
   - Render production-style Java code snippets (e.g. `@Controller`, `@Service`, `@Repository`, `@Entity` or DTOs, and HTML templates) for the active step in the MVC flow.
   - Provide a copying interface/tab for complete Java files.
5. **E2E Testing & Verification (Milestone 5)**
   - Run the E2E test suite to achieve 100% pass rate.
6. **Adversarial Hardening (Milestone 6)**
   - Spawn Challenger to verify edge-case robustness of the interactive page.
7. **Forensic Audit & Handoff (Milestone 7)**
   - Run the Forensic Auditor to check code integrity and confirm compliance.
8. **Detailed File-Level Data Tracking & Progressive Diagram Breakdown (Milestone 8)**
   - Update `index.html` to trace specific Java files interacting at each step (e.g., `StudentController.java` calling `StudentService.java`) showing exactly what data is passed.
   - Adjust `index.html` to break down the visual diagram into progressive visual steps (e.g., layers/arrows fade in or reveal progressively as the simulation advances).
   - Update `PROJECT.md` to document the new features and update the milestones table.
9. **E2E Test Suite Update & Verification (Milestone 9)**
   - Update E2E test cases in `tests/test_mvc_flow.py` and `tests/test_adversarial_ui.py` to programmatically assert the file-level tracking info and progressive diagram opacity states.
   - Run `tests/run_tests.py` using worker to verify all tests pass.
   - Update `TEST_READY.md` and `TEST_INFRA.md` with updated test results and test specifications.
10. **Forensic Audit for R4 & R5 (Milestone 10)**
    - Run the Forensic Auditor to ensure code integrity (no hardcoded/cheating responses) and verify overall compliance.

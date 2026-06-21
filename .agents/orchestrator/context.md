# Project Context

## Project Name
Java MVC Educational Simulation (Interactive Web Application)

## Environment Context
- OS: Windows
- Project Root: e:\test\mvc-simulation
- Existing files:
  - `index.html` (main web application containing simulation UI, state machine, and embedded code snippets)
  - `src/` (layered production-style Java codebase in Student scenario: controller, service, repository, model, dto, view, main, utils)
  - `tests/` (Python E2E test suite using pytest and Playwright: test_mvc_flow.py, test_adversarial_ui.py, run_tests.py)
  - `PROJECT.md` (project spec, code layout, interface contracts, milestones table)
  - `TEST_INFRA.md` (E2E testing architecture, methodology, coverage details)
  - `TEST_READY.md` (attestation of test run success)

## Requirements Summary
- R1. Interactive MVC Flow Visualization: Visual request/response lifecycle.
- R2. Contextual Scenario & Explanations: Student Management System mock scenario with class responsibility explanations.
- R3. Reference Java Code Generation: Contextual production-style Java code snippets and file copying.
- R4. Detailed File-Level Data Tracking (NEW): Trace specific Java files interacting at each step (e.g. StudentController.java ➔ StudentService.java) and show exact data payload passed.
- R5. Progressive Diagram Breakdown (NEW): Break down the architectural diagram into smaller, progressive visual steps instead of showing all statically at once.

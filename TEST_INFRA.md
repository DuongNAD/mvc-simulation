# Java MVC Educational Simulation E2E Test Infrastructure

This document details the E2E testing architecture, methodology, and coverage for the Java MVC Educational Simulation frontend.

## 1. Test Philosophy & Methodology

The E2E test suite adopts an **opaque-box, requirement-driven testing philosophy**. The goal is to verify that the application behaves exactly as expected from the perspective of an end-user, interacting purely with the DOM.
- **No Implementation Coupling**: Tests interact only with standard DOM identifiers (`#studentName`, `#startBtn`, `#nextBtn`, `#prevBtn`) and verify the active visual states.
- **Runtime Polyfill Injection Strategy**: A dynamic polyfill strategy is utilized. When running the test suite, the helper `polyfill_stepping_if_needed(page)` checks if stepping buttons and custom logic are natively implemented in the `index.html`. If not, it evaluate-injects them at runtime. This decouples the E2E test suite development from the HTML/JS parallel updates.

## 2. Test Architecture

The E2E test suite consists of two main components:
1. **Custom Test Runner (`tests/run_tests.py`)**: A programmatic wrapper that configures python stdout/stderr encoding, sets up the python environment path, executes the test suite via `pytest`, collects the execution results, prints a summary, and exits with code `0` on success.
2. **E2E Test Suite (`tests/test_mvc_flow.py`)**: Employs the `Playwright Sync API` and `pytest` to spin up a headless Chromium browser instance per test function, navigates to the local file URL, and interacts with the simulation.

## 3. Test Coverage Inventory

The test suite is structured into **four distinct tiers** of progressive test verification:

### Tier 1: Happy Paths & Baseline Layout
- `test_tier1_dom_elements_exist`: Asserts the presence of all core layout boxes (`#main-layer`, `#view-layer`, `#controller-layer`, `#service-layer`, `#repo-layer`, `#model-layer`), inputs, buttons, console output, database, and connection arrows on load.
- `test_tier1_initial_state`: Confirms the default initial state values and styling classes (inactive classes, initial status texts, default input value "Nguyễn Văn A", empty payload status).

### Tier 2: Boundary Inputs & Validation State Machine
- `test_tier2_empty_name_validation`: Validates that starting the simulation with an empty student name input triggers the error banner (`#error-message` loses `hidden`) and halts progress (no active highlights on layers).
- `test_tier2_whitespace_name_validation`: Verifies that a name containing only whitespace is correctly trimmed, rejected, and triggers the error validation.
- `test_tier2_button_disabled_during_execution`: Asserts that once a valid simulation run starts, the main action button `#startBtn` is locked/disabled and marked with cursor styling (`opacity-50` and `cursor-not-allowed`) to prevent concurrent executions.

### Tier 3: Visual State & DOM Transitions
- `test_tier3_manual_stepping_flow`: Tests a complete stepping simulation sequence. Traces highlights and status texts step-by-step from Main -> Controller -> Service -> Repo -> Model -> Repo/Service/Controller -> View. Asserts specific `.active` classes on layers/arrows, payload monitor texts, and button enablement/disablement. Works adaptively on both native and polyfilled stepping implementations. Additionally asserts that `#file-tracking-display` exists and displays the correct file-level tracking texts for each step, and that layers and arrows transition between `opacity-10` and `opacity-100` progressively as they are reached.
- `test_tier3_manual_stepping_backward`: Validates stepping backward via `#prevBtn` restores the previous highlights, resets states, and successfully rolls back database content if stepping back from the Model insertion step. Verifies that opacities of layers and arrows are correctly reverted when stepping backward.

### Tier 4: Consecutive Runs & Data Accumulation
- `test_tier4_multi_run_accumulation`: Executes multiple sequential student registration runs back-to-back. Verifies that the simulated database (`#database-content` container) retains records and exhibits cumulative state persistence (e.g. showing both student records at the end of the second run).
